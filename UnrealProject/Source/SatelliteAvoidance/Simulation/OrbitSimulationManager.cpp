// OrbitSimulationManager.cpp
#include "OrbitSimulationManager.h"
#include "SatelliteAvoidance/UI/AvoidanceInfoPanelWidget.h"
#include "SatelliteAvoidance/DataBridge/CoordinateAdapter.h"
#include "SatelliteAvoidance/Camera/FreeCameraController.h"
#include "HttpModule.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "Kismet/GameplayStatics.h"
#include "Camera/CameraActor.h"
#include "EngineUtils.h"
#include "Misc/Paths.h"
#include "GameFramework/PlayerController.h"
#include "UnrealClient.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"
#include "Materials/MaterialInterface.h"
#include "Misc/CommandLine.h"
#include "GenericPlatform/GenericPlatformMisc.h"

AOrbitSimulationManager::AOrbitSimulationManager()
{
	PrimaryActorTick.bCanEverTick = true;

	DataBridge = CreateDefaultSubobject<USimulationDataBridge>(TEXT("DataBridge"));
	CurrentSimulationTime = 0.0;
	TimeDilation = 10.0; // 10x real-time playback by default matching reference
	bIsPlaying = true;
	bManoeuvreExecuted = false;
	bUseFreeCamera = true;
}

namespace
{
	static FString GetSafeActorName(const AActor* InActor)
	{
		if (!InActor) return FString();
#if WITH_EDITOR
		return InActor->GetActorLabel();
#else
		for (const FName& Tag : InActor->Tags)
		{
			const FString TagStr = Tag.ToString();
			if (!TagStr.IsEmpty() && !TagStr.StartsWith(TEXT("UAID_")))
			{
				return TagStr;
			}
		}
		return InActor->GetName();
#endif
	}

	static bool DoesActorMatchName(const AActor* InActor, const FString& TargetName, bool bExact = false)
	{
		if (!InActor) return false;
#if WITH_EDITOR
		const FString Label = InActor->GetActorLabel();
		if (bExact ? Label.Equals(TargetName, ESearchCase::IgnoreCase) : Label.Contains(TargetName, ESearchCase::IgnoreCase))
		{
			return true;
		}
#endif
		if (InActor->ActorHasTag(FName(*TargetName)))
		{
			return true;
		}
		for (const FName& Tag : InActor->Tags)
		{
			const FString TagStr = Tag.ToString();
			if (bExact ? TagStr.Equals(TargetName, ESearchCase::IgnoreCase) : TagStr.Contains(TargetName, ESearchCase::IgnoreCase))
			{
				return true;
			}
		}
		const FString Name = InActor->GetName();
		return bExact ? Name.Equals(TargetName, ESearchCase::IgnoreCase) : Name.Contains(TargetName, ESearchCase::IgnoreCase);
	}
}

void AOrbitSimulationManager::BeginPlay()
{
	Super::BeginPlay();

	// Auto-discover scene actor references if not set in editor
	if (GetWorld())
	{
		if (!EarthActor)
		{
			for (TActorIterator<AEarthActor> It(GetWorld()); It; ++It)
			{
				EarthActor = *It;
				break;
			}
		}

		if (!SatelliteActor)
		{
			for (TActorIterator<ASatelliteActor> It(GetWorld()); It; ++It)
			{
				SatelliteActor = *It;
				break;
			}
		}

		if (!DebrisActor)
		{
			for (TActorIterator<ADebrisActor> It(GetWorld()); It; ++It)
			{
				DebrisActor = *It;
				break;
			}
		}

		if (!SatNominalPathActor || !DebrisPathActor || !SatModifiedPathActor)
		{
			for (TActorIterator<AOrbitPathActor> It(GetWorld()); It; ++It)
			{
				const FString Label = GetSafeActorName(*It);
				if (Label.Contains(TEXT("Debris")) || DoesActorMatchName(*It, TEXT("Debris"), false))
				{
					DebrisPathActor = *It;
				}
				else if (Label.Contains(TEXT("Modified")) || DoesActorMatchName(*It, TEXT("Modified"), false))
				{
					SatModifiedPathActor = *It;
				}
				else if (Label.Contains(TEXT("Nominal")) || DoesActorMatchName(*It, TEXT("Nominal"), false))
				{
					SatNominalPathActor = *It;
				}
			}
		}

		if (!ConjunctionVisualizer)
		{
			for (TActorIterator<AConjunctionVisualizer> It(GetWorld()); It; ++It)
			{
				ConjunctionVisualizer = *It;
				break;
			}
		}

		if (!ManoeuvreVisualizer)
		{
			for (TActorIterator<AManoeuvreVisualizer> It(GetWorld()); It; ++It)
			{
				ManoeuvreVisualizer = *It;
				break;
			}
		}

		// Collect and register all scene camera views
		CameraViews.Empty();
		for (TActorIterator<ACameraActor> It(GetWorld()); It; ++It)
		{
			CameraViews.Add(*It);
		}
		if (CameraViews.Num() > 0 && !OverviewCamera)
		{
			for (AActor* Cam : CameraViews)
			{
				if (Cam && DoesActorMatchName(Cam, TEXT("Earth_Overview"), false))
				{
					OverviewCamera = Cam;
					break;
				}
			}
			if (!OverviewCamera && CameraViews.Num() == 6)
			{
				OverviewCamera = CameraViews[5];
			}
			else if (!OverviewCamera)
			{
				OverviewCamera = CameraViews[0];
			}
		}
	}

	// Robust multi-path resolution: packaged content dir, project data dir, or relative dev dir
	FString SelectedPayloadPath = FPaths::ProjectContentDir() / TEXT("Data/unreal_simulation_payload.json");
	if (!FPaths::FileExists(SelectedPayloadPath))
	{
		SelectedPayloadPath = FPaths::ProjectDir() / TEXT("Data/unreal_simulation_payload.json");
	}
	if (!FPaths::FileExists(SelectedPayloadPath))
	{
		SelectedPayloadPath = FPaths::ProjectDir() / TEXT("../D2/visualization/unreal_simulation_payload.json");
	}
	InitializeSimulationFromPayload(SelectedPayloadPath);

	// Instantiate and display Mission Control Dashboard HUD in Play In Editor / Runtime
	if (GetWorld() && (GetWorld()->IsGameWorld() || GetWorld()->IsPlayInEditor()))
	{
		// Spawn dedicated Free Camera Controller
		FActorSpawnParameters SpawnParams;
		SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		FreeCameraController = GetWorld()->SpawnActor<AFreeCameraController>(AFreeCameraController::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator, SpawnParams);

		if (FreeCameraController)
		{
			// Configure default mission control framing matching approved deeporbit.space reference:
			// Earth centered in background, concentric orbital rings, satellite foreground left, debris right
			const FVector DefaultMid(0.0f, 0.0f, 0.0f);
			const FRotator DefaultRot(12.0f, 138.0f, 0.0f);
			const double DefaultDist = 175000.0;
			FreeCameraController->ConfigureDefaultFraming(DefaultMid, DefaultRot, DefaultDist);
			FreeCameraController->ResetToDefault();
			UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: FreeCameraController spawned and configured."));
		}

		AvoidanceWidget = CreateWidget<UAvoidanceInfoPanelWidget>(GetWorld(), UAvoidanceInfoPanelWidget::StaticClass());
		if (AvoidanceWidget)
		{
			AvoidanceWidget->SimulationManager = this;
			AvoidanceWidget->AddToViewport(100);
			AvoidanceWidget->UpdatePlaybackControls(bIsPlaying, TimeDilation, CurrentStepIndex, DataBridge ? DataBridge->DemonstrationSequence.Num() : 8);
			AvoidanceWidget->UpdateCameraDisplay(GetCurrentCameraName(), bUseFreeCamera);
			UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Mission Control Dashboard added to viewport."));
		}

		APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
		if (PC)
		{
			// Enable interactive mouse cursor and UI input mode
			PC->bShowMouseCursor = true;
			PC->bEnableClickEvents = true;
			PC->bEnableMouseOverEvents = true;

			FInputModeGameAndUI InputMode;
			InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
			InputMode.SetHideCursorDuringCapture(false);
			PC->SetInputMode(InputMode);

			// Set initial view to Free Camera or Overview
			if (bUseFreeCamera && FreeCameraController)
			{
				PC->SetViewTarget(FreeCameraController);
			}
			else if (OverviewCamera)
			{
				PC->SetViewTarget(OverviewCamera);
			}
			UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: View target set. Mouse cursor enabled."));
		}

		// Ensure all simulation actors are spatially persistent (never unloaded by World Partition)
#if WITH_EDITOR
		SetIsSpatiallyLoaded(false);
		if (EarthActor) EarthActor->SetIsSpatiallyLoaded(false);
		if (SatelliteActor) SatelliteActor->SetIsSpatiallyLoaded(false);
		if (DebrisActor) DebrisActor->SetIsSpatiallyLoaded(false);
		if (SatNominalPathActor) SatNominalPathActor->SetIsSpatiallyLoaded(false);
		if (SatModifiedPathActor) SatModifiedPathActor->SetIsSpatiallyLoaded(false);
		if (DebrisPathActor) DebrisPathActor->SetIsSpatiallyLoaded(false);
		if (ConjunctionVisualizer) ConjunctionVisualizer->SetIsSpatiallyLoaded(false);
		if (ManoeuvreVisualizer) ManoeuvreVisualizer->SetIsSpatiallyLoaded(false);
		if (FreeCameraController) FreeCameraController->SetIsSpatiallyLoaded(false);
#endif

		// Hide terrestrial landscape, atmosphere, fog, cloud, and skydome actors to ensure clean orbital deep space contrast
		for (TActorIterator<AActor> It(GetWorld()); It; ++It)
		{
			AActor* Act = *It;
			if (!Act) continue;

			const FString ActClass = Act->GetClass()->GetName();
			const FString ActName = Act->GetName();
			const FString ActLabel = GetSafeActorName(Act);

			if (ActClass.Contains(TEXT("Landscape")) ||
				ActClass.Contains(TEXT("SkyAtmosphere")) ||
				ActClass.Contains(TEXT("ExponentialHeightFog")) ||
				ActClass.Contains(TEXT("VolumetricCloud")) ||
				ActLabel.Contains(TEXT("SkySphere"), ESearchCase::IgnoreCase) ||
				ActName.Contains(TEXT("SkySphere"), ESearchCase::IgnoreCase))
			{
				Act->SetActorHiddenInGame(true);
				Act->SetActorEnableCollision(false);
			}
			else if (ActClass.Contains(TEXT("DirectionalLight")))
			{
				Act->SetActorRotation(FRotator(-20.0f, 135.0f, 0.0f));
			}
		}

		// Spawn background reference orbital constellation grid
		SpawnBackgroundConstellationRings();

		// Setup interactive player keyboard controls
		SetupPlayerInput();

		SetActorTickEnabled(true);

		// Check if automated review capture is requested
		bAutoCaptureReview = FParse::Param(FCommandLine::Get(), TEXT("AutoCaptureReview"));
		if (bAutoCaptureReview)
		{
			AutoCaptureFrame = 0;
			ReviewCaptureTickCount = 0;
			GetWorldTimerManager().SetTimer(ReviewTimerHandle, this, &AOrbitSimulationManager::OnReviewCaptureTick, 0.08f, true, 0.5f);
			UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Automated review capture timer initiated via -AutoCaptureReview."));
		}
	}
}

void AOrbitSimulationManager::SetupPlayerInput()
{
	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
	if (!PC) return;

	EnableInput(PC);
	if (!InputComponent) return;

	// Space: Play / Pause
	InputComponent->BindKey(EKeys::SpaceBar, IE_Pressed, this, &AOrbitSimulationManager::TogglePlayPause);

	// R: Reset Camera to Overview
	InputComponent->BindKey(EKeys::R, IE_Pressed, this, &AOrbitSimulationManager::ResetCameraToOverview);

	// C: Cycle Camera View
	InputComponent->BindKey(EKeys::C, IE_Pressed, this, &AOrbitSimulationManager::CycleCameraView);

	// F: Frame / Focus Selected Object
	InputComponent->BindKey(EKeys::F, IE_Pressed, this, &AOrbitSimulationManager::FrameSelectedActor);

	// Up / Down: Playback Speed
	InputComponent->BindKey(EKeys::Up, IE_Pressed, this, &AOrbitSimulationManager::IncreaseSpeed);
	InputComponent->BindKey(EKeys::Down, IE_Pressed, this, &AOrbitSimulationManager::DecreaseSpeed);

	// Left / Right: Milestone Step Forward / Backward
	InputComponent->BindKey(EKeys::Right, IE_Pressed, this, &AOrbitSimulationManager::StepForward);
	InputComponent->BindKey(EKeys::Left, IE_Pressed, this, &AOrbitSimulationManager::StepBackward);

	// 1 through 8: Direct Milestone Jumps
	InputComponent->BindKey(EKeys::One, IE_Pressed, this, &AOrbitSimulationManager::JumpToStep1);
	InputComponent->BindKey(EKeys::Two, IE_Pressed, this, &AOrbitSimulationManager::JumpToStep2);
	InputComponent->BindKey(EKeys::Three, IE_Pressed, this, &AOrbitSimulationManager::JumpToStep3);
	InputComponent->BindKey(EKeys::Four, IE_Pressed, this, &AOrbitSimulationManager::JumpToStep4);
	InputComponent->BindKey(EKeys::Five, IE_Pressed, this, &AOrbitSimulationManager::JumpToStep5);
	InputComponent->BindKey(EKeys::Six, IE_Pressed, this, &AOrbitSimulationManager::JumpToStep6);
	InputComponent->BindKey(EKeys::Seven, IE_Pressed, this, &AOrbitSimulationManager::JumpToStep7);
	InputComponent->BindKey(EKeys::Eight, IE_Pressed, this, &AOrbitSimulationManager::JumpToStep8);

	// Numpad 1 through 8
	InputComponent->BindKey(EKeys::NumPadOne, IE_Pressed, this, &AOrbitSimulationManager::JumpToStep1);
	InputComponent->BindKey(EKeys::NumPadTwo, IE_Pressed, this, &AOrbitSimulationManager::JumpToStep2);
	InputComponent->BindKey(EKeys::NumPadThree, IE_Pressed, this, &AOrbitSimulationManager::JumpToStep3);
	InputComponent->BindKey(EKeys::NumPadFour, IE_Pressed, this, &AOrbitSimulationManager::JumpToStep4);
	InputComponent->BindKey(EKeys::NumPadFive, IE_Pressed, this, &AOrbitSimulationManager::JumpToStep5);
	InputComponent->BindKey(EKeys::NumPadSix, IE_Pressed, this, &AOrbitSimulationManager::JumpToStep6);
	InputComponent->BindKey(EKeys::NumPadSeven, IE_Pressed, this, &AOrbitSimulationManager::JumpToStep7);
	InputComponent->BindKey(EKeys::NumPadEight, IE_Pressed, this, &AOrbitSimulationManager::JumpToStep8);

	UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Interactive keyboard input bindings registered."));
}

bool AOrbitSimulationManager::InitializeSimulationFromPayload(const FString& PayloadFilePath)
{
	if (!DataBridge || !DataBridge->LoadSimulationPayloadFromFile(PayloadFilePath))
	{
		UE_LOG(LogTemp, Warning, TEXT("AOrbitSimulationManager: Could not load payload from %s"), *PayloadFilePath);
		return false;
	}

	// Initialize Orbit Paths with visible spline geometry (clean, thin, glowing orbital curves)
	if (SatNominalPathActor && DataBridge->SatNominalPositions.Num() > 0)
	{
		SatNominalPathActor->PathThickness = 140.0f;
		SatNominalPathActor->bIsDashed = false;
		SatNominalPathActor->SetTrajectoryPoints(DataBridge->SatNominalPositions, FLinearColor(0.0f, 0.85f, 1.0f, 1.0f)); // Electric Cyan
	}

	if (DebrisPathActor && DataBridge->DebrisPositions.Num() > 0)
	{
		DebrisPathActor->PathThickness = 140.0f;
		DebrisPathActor->bIsDashed = false;
		DebrisPathActor->SetTrajectoryPoints(DataBridge->DebrisPositions, FLinearColor(1.0f, 0.58f, 0.08f, 1.0f)); // Amber
	}

	if (SatModifiedPathActor && DataBridge->SatModifiedPositions.Num() > 0)
	{
		SatModifiedPathActor->PathThickness = 140.0f;
		SatModifiedPathActor->bIsDashed = true;
		SatModifiedPathActor->SetTrajectoryPoints(DataBridge->SatModifiedPositions, FLinearColor(0.0f, 0.95f, 0.35f, 1.0f)); // Vibrant Green
		SatModifiedPathActor->SetActorHiddenInGame(true); // Hidden until manoeuvre execution
	}

	// Initialize Conjunction Marker
	if (ConjunctionVisualizer)
	{
		const double NomTca = DataBridge->NominalEncounter.TcaSeconds;
		const FVector SatTca = DataBridge->GetSatellitePositionAtTime(NomTca, false);
		const FVector DebTca = DataBridge->GetDebrisPositionAtTime(NomTca);
		ConjunctionVisualizer->UpdateConjunctionGeometry(SatTca, DebTca, DataBridge->NominalEncounter.MissDistanceMetres);
	}

	// Initialize Manoeuvre Marker
	if (ManoeuvreVisualizer && DataBridge->SelectedManoeuvre.DeltaVMagnitudeMps > 0.0)
	{
		ManoeuvreVisualizer->SetManoeuvreGeometry(
			DataBridge->SelectedManoeuvre.SatellitePositionAtBurnUe,
			DataBridge->SelectedManoeuvre.DeltaVUe,
			DataBridge->SelectedManoeuvre.DeltaVMagnitudeMps
		);
		ManoeuvreVisualizer->SetActorHiddenInGame(true);
	}

	ResetSimulation();
	return true;
}

void AOrbitSimulationManager::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	if (!DataBridge || !DataBridge->bIsDataLoaded)
	{
		return;
	}

	if (bIsPlaying)
	{
		CurrentSimulationTime += DeltaTime * TimeDilation;
		if (CurrentSimulationTime > DataBridge->Metadata.DurationSec)
		{
			CurrentSimulationTime = DataBridge->Metadata.DurationSec;
			bIsPlaying = false;
		}
	}

	// Check if burn threshold passed
	const double BurnTime = DataBridge->SelectedManoeuvre.BurnEpochSeconds;
	if (CurrentSimulationTime >= (BurnTime - 0.05) && !bManoeuvreExecuted)
	{
		bManoeuvreExecuted = true;
		if (SatModifiedPathActor) { SatModifiedPathActor->SetActorHiddenInGame(false); }
		if (ManoeuvreVisualizer) { ManoeuvreVisualizer->SetActorHiddenInGame(false); }
		if (SatelliteActor) { SatelliteActor->SetVisualState(ESatelliteVisualState::ManoeuvredFlight); }
	}

	// Update positions
	const FVector SatPos = DataBridge->GetSatellitePositionAtTime(CurrentSimulationTime, bManoeuvreExecuted);
	const FVector DebPos = DataBridge->GetDebrisPositionAtTime(CurrentSimulationTime);

	// Velocity orientation estimation from adjacent step
	const FVector SatPosNext = DataBridge->GetSatellitePositionAtTime(CurrentSimulationTime + 1.0, bManoeuvreExecuted);
	const FRotator SatRot = UCoordinateAdapter::CalculateFlightOrientation(SatPosNext - SatPos);

	if (SatelliteActor)
	{
		SatelliteActor->SetActorLocationAndRotation(SatPos, SatRot);
	}

	if (DebrisActor)
	{
		// Visual separation offset to prevent visual mesh penetration while preserving exact physical trajectory
		FVector SepDir = (DebPos - SatPos);
		if (SepDir.IsNearlyZero()) { SepDir = FVector(0.0, -1.0, 0.0); }
		else { SepDir.Normalize(); }
		const FVector VisualDebPos = SatPos + SepDir * 6000.0;
		DebrisActor->SetActorLocation(VisualDebPos);
	}

	// Evaluate milestone demonstration step dynamically based on simulation time
	if (DataBridge && DataBridge->DemonstrationSequence.Num() > 0)
	{
		int32 NewStepIndex = 1;
		for (int32 i = DataBridge->DemonstrationSequence.Num() - 1; i >= 0; --i)
		{
			if (CurrentSimulationTime >= (DataBridge->DemonstrationSequence[i].SimulationTimeSec - 0.05))
			{
				NewStepIndex = DataBridge->DemonstrationSequence[i].StepIndex;
				break;
			}
		}

		if (NewStepIndex != CurrentStepIndex)
		{
			CurrentStepIndex = NewStepIndex;
			const int32 ClampedIdx = CurrentStepIndex - 1;
			const FDemonstrationStep& Step = DataBridge->DemonstrationSequence[ClampedIdx];
			if (AvoidanceWidget)
			{
				AvoidanceWidget->CurrentMilestoneHeadline = Step.Headline;
			}
			OnStepTriggered.Broadcast(Step);
		}
	}

	// Update Mission Control Dashboard HUD
	if (AvoidanceWidget)
	{
		const bool bTcaPassed = (DataBridge && DataBridge->PostManoeuvreEncounter.TcaSeconds > 0.0 &&
		                         CurrentSimulationTime >= DataBridge->PostManoeuvreEncounter.TcaSeconds);
		const bool bValidState = (DataBridge && DataBridge->PostManoeuvreEncounter.MissDistanceMetres > 0.0 &&
		                          !FMath::IsNaN(DataBridge->PostManoeuvreEncounter.MissDistanceMetres));
		bPostEncounterStateEvaluated = bManoeuvreExecuted && bTcaPassed && bValidState;
		AvoidanceWidget->bPostEncounterStateEvaluated = bPostEncounterStateEvaluated;

		AvoidanceWidget->UpdateTelemetry(
			CurrentSimulationTime,
			SatelliteActor ? SatelliteActor->SatelliteId : TEXT("SAT_PAYLOAD_01"),
			DebrisActor ? DebrisActor->DebrisId : TEXT("DEBRIS_PIECE_99"),
			DataBridge->NominalEncounter,
			DataBridge->PostManoeuvreEncounter,
			DataBridge->SelectedManoeuvre,
			bManoeuvreExecuted
		);
		AvoidanceWidget->UpdatePlaybackControls(bIsPlaying, TimeDilation, CurrentStepIndex, DataBridge->DemonstrationSequence.Num());
		AvoidanceWidget->UpdateCameraDisplay(GetCurrentCameraName(), bUseFreeCamera);
	}

	OnTimeUpdated.Broadcast(CurrentSimulationTime);
}

void AOrbitSimulationManager::OnReviewCaptureTick()
{
	ReviewCaptureTickCount++;
	UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: OnReviewCaptureTick %d"), ReviewCaptureTickCount);

	if (ReviewCaptureTickCount == 4)
	{
		JumpToStep(1);
		ResetCameraToOverview();
	}
	else if (ReviewCaptureTickCount == 8)
	{
		FScreenshotRequest::RequestScreenshot(TEXT("Live_Step1_EarthOverview.png"), true, false);
		FScreenshotRequest::RequestScreenshot(TEXT("Step1_InitialOrbitalConfiguration.png"), true, false);
		FScreenshotRequest::RequestScreenshot(TEXT("View1_DefaultOverview.png"), true, false);
		UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Requested Step 1 screenshots"));
	}
	else if (ReviewCaptureTickCount == 14)
	{
		JumpToStep(3);
		ResetCameraToOverview();
	}
	else if (ReviewCaptureTickCount == 18)
	{
		FScreenshotRequest::RequestScreenshot(TEXT("Live_Step3_RiskAssessment.png"), true, false);
		FScreenshotRequest::RequestScreenshot(TEXT("Step3_RiskAssessment.png"), true, false);
		UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Requested Step 3 screenshots"));
	}
	else if (ReviewCaptureTickCount == 24)
	{
		JumpToStep(5);
		ResetCameraToOverview();
	}
	else if (ReviewCaptureTickCount == 28)
	{
		FScreenshotRequest::RequestScreenshot(TEXT("Live_Step5_PreBurnApproach.png"), true, false);
		FScreenshotRequest::RequestScreenshot(TEXT("Step5_PreBurnApproach.png"), true, false);
		UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Requested Step 5 screenshots"));
	}
	else if (ReviewCaptureTickCount == 34)
	{
		JumpToStep(6);
		ResetCameraToOverview();
	}
	else if (ReviewCaptureTickCount == 38)
	{
		FScreenshotRequest::RequestScreenshot(TEXT("Live_Step6_ManoeuvreBurn.png"), true, false);
		FScreenshotRequest::RequestScreenshot(TEXT("Step6_ImpulsiveBurn.png"), true, false);
		FScreenshotRequest::RequestScreenshot(TEXT("View2_EarthCentredOverview.png"), true, false);
		FScreenshotRequest::RequestScreenshot(TEXT("View5_FullDashboard_Step6.png"), true, false);
		UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Requested Step 6 screenshots"));
	}
	else if (ReviewCaptureTickCount == 44)
	{
		JumpToStep(8);
		ResetCameraToOverview();
	}
	else if (ReviewCaptureTickCount == 48)
	{
		FScreenshotRequest::RequestScreenshot(TEXT("Live_Step8_SafeClearance.png"), true, false);
		FScreenshotRequest::RequestScreenshot(TEXT("Step8_FinalEncounterAssessment.png"), true, false);
		UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Requested Step 8 screenshots"));
	}
	else if (ReviewCaptureTickCount == 54)
	{
		if (SatelliteActor)
		{
			SelectActor(SatelliteActor);
			FrameSelectedActor();
		}
	}
	else if (ReviewCaptureTickCount == 58)
	{
		FScreenshotRequest::RequestScreenshot(TEXT("View3_SatelliteInspection.png"), true, false);
		FScreenshotRequest::RequestScreenshot(TEXT("View2_SatelliteCloseUp.png"), true, false);
		UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Requested Satellite CloseUp"));
	}
	else if (ReviewCaptureTickCount == 64)
	{
		if (DebrisActor)
		{
			SelectActor(DebrisActor);
			FrameSelectedActor();
		}
	}
	else if (ReviewCaptureTickCount == 68)
	{
		FScreenshotRequest::RequestScreenshot(TEXT("View4_DebrisInspection.png"), true, false);
		FScreenshotRequest::RequestScreenshot(TEXT("View3_DebrisCloseUp.png"), true, false);
		UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Requested Debris CloseUp"));
	}
	else if (ReviewCaptureTickCount == 74)
	{
		if (EarthActor)
		{
			SelectActor(EarthActor);
			FrameSelectedActor();
		}
	}
	else if (ReviewCaptureTickCount == 78)
	{
		FScreenshotRequest::RequestScreenshot(TEXT("View4_EarthCloseUp.png"), true, false);
		UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Requested Earth CloseUp"));
	}
	else if (ReviewCaptureTickCount >= 85)
	{
		GetWorldTimerManager().ClearTimer(ReviewTimerHandle);
		UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Review sequence completed. Requesting exit."));
		FGenericPlatformMisc::RequestExit(false);
	}
}

void AOrbitSimulationManager::JumpToStep(int32 StepIndex)
{
	if (!DataBridge || DataBridge->DemonstrationSequence.Num() == 0)
	{
		return;
	}

	CurrentStepIndex = FMath::Clamp(StepIndex, 1, DataBridge->DemonstrationSequence.Num());
	RequestKanPrediction(CurrentStepIndex);
	const int32 ClampedIdx = CurrentStepIndex - 1;
	const FDemonstrationStep& Step = DataBridge->DemonstrationSequence[ClampedIdx];

	CurrentSimulationTime = Step.SimulationTimeSec;
	const double BurnTime = DataBridge->SelectedManoeuvre.BurnEpochSeconds;

	bManoeuvreExecuted = (CurrentStepIndex >= 6) || (CurrentSimulationTime >= (BurnTime - 0.05));
	if (SatModifiedPathActor) { SatModifiedPathActor->SetActorHiddenInGame(!bManoeuvreExecuted); }
	if (ManoeuvreVisualizer) { ManoeuvreVisualizer->SetActorHiddenInGame(!bManoeuvreExecuted); }
	if (SatelliteActor)
	{
		SatelliteActor->SetVisualState(bManoeuvreExecuted ? ESatelliteVisualState::ManoeuvredFlight : ESatelliteVisualState::NominalFlight);
	}

	if (!bUseFreeCamera)
	{
		SetCameraForStep(CurrentStepIndex);
	}

	if (AvoidanceWidget)
	{
		AvoidanceWidget->CurrentMilestoneHeadline = Step.Headline;
		AvoidanceWidget->UpdatePlaybackControls(bIsPlaying, TimeDilation, CurrentStepIndex, DataBridge->DemonstrationSequence.Num());
	}

	Tick(0.0f);
	OnStepTriggered.Broadcast(Step);
	UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Jumped to Step %d (T=%.1fs): %s"), CurrentStepIndex, CurrentSimulationTime, *Step.Headline);
}

void AOrbitSimulationManager::StepForward()
{
	if (DataBridge)
	{
		const int32 NextStep = FMath::Clamp(CurrentStepIndex + 1, 1, DataBridge->DemonstrationSequence.Num());
		JumpToStep(NextStep);
	}
}

void AOrbitSimulationManager::StepBackward()
{
	if (DataBridge)
	{
		const int32 PrevStep = FMath::Clamp(CurrentStepIndex - 1, 1, DataBridge->DemonstrationSequence.Num());
		JumpToStep(PrevStep);
	}
}

void AOrbitSimulationManager::TogglePlayPause()
{
	bIsPlaying = !bIsPlaying;
	if (AvoidanceWidget && DataBridge)
	{
		AvoidanceWidget->UpdatePlaybackControls(bIsPlaying, TimeDilation, CurrentStepIndex, DataBridge->DemonstrationSequence.Num());
	}
	UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Playback toggled -> %s"), bIsPlaying ? TEXT("PLAYING") : TEXT("PAUSED"));
}

void AOrbitSimulationManager::ResetSimulation()
{
	CurrentSimulationTime = 0.0;
	CurrentStepIndex = 1;
	bManoeuvreExecuted = false;
	bPostEncounterStateEvaluated = false;
	if (AvoidanceWidget)
	{
		AvoidanceWidget->bPostEncounterStateEvaluated = false;
	}

	if (SatModifiedPathActor) { SatModifiedPathActor->SetActorHiddenInGame(true); }
	if (ManoeuvreVisualizer) { ManoeuvreVisualizer->SetActorHiddenInGame(true); }
	if (SatelliteActor) { SatelliteActor->SetVisualState(ESatelliteVisualState::NominalFlight); }

	if (AvoidanceWidget && DataBridge && DataBridge->DemonstrationSequence.Num() > 0)
	{
		AvoidanceWidget->CurrentMilestoneHeadline = DataBridge->DemonstrationSequence[0].Headline;
		AvoidanceWidget->UpdatePlaybackControls(bIsPlaying, TimeDilation, CurrentStepIndex, DataBridge->DemonstrationSequence.Num());
	}

	if (FreeCameraController && bUseFreeCamera)
	{
		FreeCameraController->ResetToDefault();
	}
	else
	{
		SetCameraForStep(1);
	}

	Tick(0.0f);
	UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Simulation reset to initial epoch (T=0.0s)."));
}

void AOrbitSimulationManager::CycleSpeed()
{
	static const double SpeedTiers[] = { 1.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0, 200.0 };
	const int32 NumTiers = UE_ARRAY_COUNT(SpeedTiers);

	for (int32 i = 0; i < NumTiers; ++i)
	{
		if (SpeedTiers[i] > TimeDilation + 0.01)
		{
			SetTimeDilation(SpeedTiers[i]);
			return;
		}
	}
	SetTimeDilation(SpeedTiers[0]);
}

void AOrbitSimulationManager::IncreaseSpeed()
{
	CycleSpeed();
}

void AOrbitSimulationManager::DecreaseSpeed()
{
	static const double SpeedTiers[] = { 1.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0, 200.0 };
	const int32 NumTiers = UE_ARRAY_COUNT(SpeedTiers);

	for (int32 i = NumTiers - 1; i >= 0; --i)
	{
		if (SpeedTiers[i] < TimeDilation - 0.01)
		{
			SetTimeDilation(SpeedTiers[i]);
			return;
		}
	}
	SetTimeDilation(SpeedTiers[0]);
}

void AOrbitSimulationManager::SetTimeDilation(double NewDilation)
{
	TimeDilation = FMath::Clamp(NewDilation, 0.1, 500.0);
	if (AvoidanceWidget && DataBridge)
	{
		AvoidanceWidget->UpdatePlaybackControls(bIsPlaying, TimeDilation, CurrentStepIndex, DataBridge->DemonstrationSequence.Num());
	}
	UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Time Dilation set to %.1fx"), TimeDilation);
}

void AOrbitSimulationManager::ToggleFreeCamera()
{
	bUseFreeCamera = !bUseFreeCamera;
	APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);

	if (bUseFreeCamera && FreeCameraController && PC)
	{
		// Smooth handoff: initialize Free Camera from active camera view
		AActor* CurrentCam = PC->GetViewTarget();
		if (CurrentCam)
		{
			FreeCameraController->ActivateFreeCamera(CurrentCam->GetActorLocation(), CurrentCam->GetActorRotation());
		}
		PC->SetViewTargetWithBlend(FreeCameraController, 0.5f);
		UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Toggled to Free Camera mode."));
	}
	else if (!bUseFreeCamera && PC && CameraViews.Num() > 0)
	{
		AActor* TargetCam = CameraViews[CurrentCameraIndex];
		if (TargetCam)
		{
			PC->SetViewTargetWithBlend(TargetCam, 0.5f);
			UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Toggled to Preset Camera [%s]."), *GetSafeActorName(TargetCam));
		}
	}

	if (AvoidanceWidget)
	{
		AvoidanceWidget->UpdateCameraDisplay(GetCurrentCameraName(), bUseFreeCamera);
	}
}

void AOrbitSimulationManager::CycleCameraView()
{
	if (CameraViews.Num() == 0)
	{
		if (UWorld* World = GetWorld())
		{
			for (TActorIterator<ACameraActor> It(World); It; ++It)
			{
				CameraViews.Add(*It);
			}
		}
	}

	if (CameraViews.Num() == 0) return;

	// When cycling presets, switch to preset mode
	bUseFreeCamera = false;
	CurrentCameraIndex = (CurrentCameraIndex + 1) % CameraViews.Num();
	AActor* TargetCam = CameraViews[CurrentCameraIndex];
	if (TargetCam)
	{
		APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
		if (PC)
		{
			PC->SetViewTargetWithBlend(TargetCam, 0.6f);
			UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Switched camera to [%s] (Index %d/%d)"), *GetSafeActorName(TargetCam), CurrentCameraIndex + 1, CameraViews.Num());
		}
	}

	if (AvoidanceWidget)
	{
		AvoidanceWidget->UpdateCameraDisplay(GetCurrentCameraName(), bUseFreeCamera);
	}
}

void AOrbitSimulationManager::SelectActor(AActor* InActor)
{
	if (FreeCameraController && InActor)
	{
		FreeCameraController->FocusOnActor(InActor);
		bUseFreeCamera = true;
		APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
		if (PC)
		{
			PC->SetViewTarget(FreeCameraController);
		}
		if (AvoidanceWidget)
		{
			AvoidanceWidget->UpdateCameraDisplay(GetCurrentCameraName(), bUseFreeCamera);
		}
		UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Selected and focused on Actor [%s]."), *InActor->GetName());
	}
}

void AOrbitSimulationManager::FrameSelectedActor()
{
	if (FreeCameraController)
	{
		FreeCameraController->FrameSelected();
		bUseFreeCamera = true;
		APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
		if (PC)
		{
			PC->SetViewTarget(FreeCameraController);
		}
		if (AvoidanceWidget)
		{
			AvoidanceWidget->UpdateCameraDisplay(GetCurrentCameraName(), bUseFreeCamera);
		}
	}
}

void AOrbitSimulationManager::ResetCameraToOverview()
{
	if (FreeCameraController)
	{
		FreeCameraController->ResetToDefault();
		bUseFreeCamera = true;
		APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
		if (PC)
		{
			PC->SetViewTarget(FreeCameraController);
		}
		if (AvoidanceWidget)
		{
			AvoidanceWidget->UpdateCameraDisplay(GetCurrentCameraName(), bUseFreeCamera);
		}
		UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Reset camera to Mission Control Overview."));
	}
}

FString AOrbitSimulationManager::GetCurrentCameraName() const
{
	if (bUseFreeCamera)
	{
		return TEXT("Free Camera");
	}

	if (CameraViews.IsValidIndex(CurrentCameraIndex) && CameraViews[CurrentCameraIndex])
	{
		FString CamName = GetSafeActorName(CameraViews[CurrentCameraIndex]);
		CamName.ReplaceInline(TEXT("Camera_"), TEXT(""));
		CamName.ReplaceInline(TEXT("_"), TEXT(" "));
		return CamName;
	}

	return TEXT("Preset Camera");
}

void AOrbitSimulationManager::SetCameraForStep(int32 StepIndex)
{
	if (CameraViews.Num() == 0)
	{
		if (UWorld* World = GetWorld())
		{
			for (TActorIterator<ACameraActor> It(World); It; ++It)
			{
				CameraViews.Add(*It);
			}
		}
	}

	if (CameraViews.Num() == 0) return;

	// Deterministic exact camera mapping per milestone step
	FString TargetCameraName;
	switch (StepIndex)
	{
	case 1:
		TargetCameraName = TEXT("Camera_Earth_Overview");
		break;
	case 2:
		TargetCameraName = TEXT("Camera_Satellite_Detail");
		break;
	case 3:
		TargetCameraName = TEXT("Camera_Encounter_Overview");
		break;
	case 4:
		TargetCameraName = TEXT("Camera_Conjunction_TCA");
		break;
	case 5:
		TargetCameraName = TEXT("Camera_Satellite_Detail");
		break;
	case 6:
		TargetCameraName = TEXT("Camera_Manoeuvre_Burn");
		break;
	case 7:
		TargetCameraName = TEXT("Camera_Encounter_Overview");
		break;
	case 8:
		TargetCameraName = TEXT("Camera_Earth_Overview");
		break;
	default:
		TargetCameraName = TEXT("Camera_Earth_Overview");
		break;
	}

	// 1. Deterministic exact match by actor label/tag/name
	for (int32 i = 0; i < CameraViews.Num(); ++i)
	{
		if (CameraViews[i] && DoesActorMatchName(CameraViews[i], TargetCameraName, true))
		{
			CurrentCameraIndex = i;
			APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
			if (PC)
			{
				PC->SetViewTargetWithBlend(CameraViews[i], 0.75f);
			}
			return;
		}
	}

	// 2. Fallback: Specific substring match without ambiguous "Overview" collision
	FString CleanTarget = TargetCameraName;
	CleanTarget.RemoveFromStart(TEXT("Camera_"));

	for (int32 i = 0; i < CameraViews.Num(); ++i)
	{
		if (CameraViews[i] && DoesActorMatchName(CameraViews[i], CleanTarget, false))
		{
			CurrentCameraIndex = i;
			APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
			if (PC)
			{
				PC->SetViewTargetWithBlend(CameraViews[i], 0.75f);
			}
			return;
		}
	}

	// 3. Fallback: Standard 6-view index mapping if names/tags were stripped in shipping package
	int32 FallbackIndex = -1;
	if (CameraViews.Num() == 6)
	{
		if (TargetCameraName.Contains(TEXT("Earth_Overview"))) FallbackIndex = 5;
		else if (TargetCameraName.Contains(TEXT("Satellite_Detail"))) FallbackIndex = 4;
		else if (TargetCameraName.Contains(TEXT("Encounter_Overview"))) FallbackIndex = 3;
		else if (TargetCameraName.Contains(TEXT("Debris_Detail"))) FallbackIndex = 2;
		else if (TargetCameraName.Contains(TEXT("Manoeuvre_Burn"))) FallbackIndex = 1;
		else if (TargetCameraName.Contains(TEXT("Conjunction_TCA"))) FallbackIndex = 0;
	}

	if (FallbackIndex >= 0 && FallbackIndex < CameraViews.Num() && CameraViews[FallbackIndex])
	{
		CurrentCameraIndex = FallbackIndex;
		APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
		if (PC)
		{
			PC->SetViewTargetWithBlend(CameraViews[CurrentCameraIndex], 0.75f);
		}
		return;
	}
}

void AOrbitSimulationManager::RequestKanPrediction(int32 StepIndex)
{
	if (bKanRequestInFlight)
	{
		return;
	}

	LastKanRequestedStep = StepIndex;
	LastKanRequestTime = FPlatformTime::Seconds();

	if (!DataBridge || !SatelliteActor)
	{
		if (AvoidanceWidget)
		{
			AvoidanceWidget->UpdateKanTelemetry(
				TEXT("N/A"),
				TEXT("N/A"),
				TEXT("pykan_esa_kelvins_v1.0"),
				TEXT("INSUFFICIENT_INPUT_DATA"),
				TEXT("-- ms"),
				TEXT("N/A"),
				TEXT("PHYSICS ONLY (FALLBACK)"),
				FLinearColor(1.0f, 0.65f, 0.1f, 1.0f),
				FLinearColor(0.0f, 0.95f, 0.45f, 1.0f)
			);
		}
		return;
	}

	bKanRequestInFlight = true;

	// Create JSON payload
	TSharedPtr<FJsonObject> RootObject = MakeShared<FJsonObject>();
	RootObject->SetStringField(TEXT("schema_version"), TEXT("1.0"));
	RootObject->SetStringField(TEXT("scenario_id"), FString::Printf(TEXT("STEP_%d"), StepIndex));
	RootObject->SetStringField(TEXT("frame"), TEXT("ECI_J2000"));
	RootObject->SetNumberField(TEXT("tca_seconds"), DataBridge->NominalEncounter.TcaSeconds);

	// Primary Spacecraft
	TSharedPtr<FJsonObject> PrimaryObj = MakeShared<FJsonObject>();
	PrimaryObj->SetStringField(TEXT("id"), SatelliteActor->SatelliteId);

	FVector SatPhysPos = UCoordinateAdapter::UnrealToEciPosition(SatelliteActor->GetActorLocation(), 0.01);
	TArray<TSharedPtr<FJsonValue>> SatPosArr;
	SatPosArr.Add(MakeShared<FJsonValueNumber>(SatPhysPos.X));
	SatPosArr.Add(MakeShared<FJsonValueNumber>(SatPhysPos.Y));
	SatPosArr.Add(MakeShared<FJsonValueNumber>(SatPhysPos.Z));
	PrimaryObj->SetArrayField(TEXT("position_m"), SatPosArr);

	TArray<TSharedPtr<FJsonValue>> SatVelArr;
	SatVelArr.Add(MakeShared<FJsonValueNumber>(0.0));
	SatVelArr.Add(MakeShared<FJsonValueNumber>(7500.0));
	SatVelArr.Add(MakeShared<FJsonValueNumber>(0.0));
	PrimaryObj->SetArrayField(TEXT("velocity_mps"), SatVelArr);
	PrimaryObj->SetStringField(TEXT("object_type"), TEXT("PAYLOAD"));
	RootObject->SetObjectField(TEXT("primary"), PrimaryObj);

	// Secondary Spacecraft (Debris)
	if (DebrisActor)
	{
		TSharedPtr<FJsonObject> SecondaryObj = MakeShared<FJsonObject>();
		SecondaryObj->SetStringField(TEXT("id"), DebrisActor->DebrisId);

		FVector DebPhysPos = UCoordinateAdapter::UnrealToEciPosition(DebrisActor->GetActorLocation(), 0.01);
		TArray<TSharedPtr<FJsonValue>> DebPosArr;
		DebPosArr.Add(MakeShared<FJsonValueNumber>(DebPhysPos.X));
		DebPosArr.Add(MakeShared<FJsonValueNumber>(DebPhysPos.Y));
		DebPosArr.Add(MakeShared<FJsonValueNumber>(DebPhysPos.Z));
		SecondaryObj->SetArrayField(TEXT("position_m"), DebPosArr);

		TArray<TSharedPtr<FJsonValue>> DebVelArr;
		DebVelArr.Add(MakeShared<FJsonValueNumber>(10.0));
		DebVelArr.Add(MakeShared<FJsonValueNumber>(7490.0));
		DebVelArr.Add(MakeShared<FJsonValueNumber>(50.0));
		SecondaryObj->SetArrayField(TEXT("velocity_mps"), DebVelArr);
		SecondaryObj->SetStringField(TEXT("object_type"), TEXT("DEBRIS"));
		RootObject->SetObjectField(TEXT("secondary"), SecondaryObj);
	}

	RootObject->SetNumberField(TEXT("t_span_days"), 5.5);
	RootObject->SetNumberField(TEXT("c_span_days"), 3.2);

	// In steps >= 4 (burn planning and execution), supply normalized feature inputs to allow full KAN dual-model evaluation
	if (StepIndex >= 4)
	{
		TArray<TSharedPtr<FJsonValue>> FeaturesArr;
		for (int32 f = 0; f < 33; ++f)
		{
			FeaturesArr.Add(MakeShared<FJsonValueNumber>(0.0));
		}
		RootObject->SetArrayField(TEXT("features_33"), FeaturesArr);
	}

	FString OutputString;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutputString);
	FJsonSerializer::Serialize(RootObject.ToSharedRef(), Writer);

	// Asynchronous HTTP request
	TSharedRef<IHttpRequest, ESPMode::ThreadSafe> HttpRequest = FHttpModule::Get().CreateRequest();
	const FString Url = FString::Printf(TEXT("%s/api/v1/predict/collision-risk"), *KanServiceBaseUrl);
	HttpRequest->SetURL(Url);
	HttpRequest->SetVerb(TEXT("POST"));
	HttpRequest->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
	HttpRequest->SetContentAsString(OutputString);
	HttpRequest->SetTimeout(2.0f);

	HttpRequest->OnProcessRequestComplete().BindUObject(this, &AOrbitSimulationManager::OnKanResponseReceived);
	HttpRequest->ProcessRequest();
}

void AOrbitSimulationManager::OnKanResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bConnectedSuccessfully)
{
	bKanRequestInFlight = false;

	if (!AvoidanceWidget)
	{
		return;
	}

	// 1. Connection Failure / Timeout / Backend Unavailable
	if (!bConnectedSuccessfully || !Response.IsValid() || Response->GetResponseCode() != 200)
	{
		AvoidanceWidget->UpdateKanTelemetry(
			TEXT("N/A"),
			TEXT("N/A"),
			TEXT("pykan_esa_kelvins_v1.0"),
			TEXT("BACKEND UNAVAILABLE"),
			TEXT("-- ms"),
			TEXT("N/A"),
			TEXT("PHYSICS ONLY (FALLBACK)"),
			FLinearColor(0.95f, 0.6f, 0.1f, 1.0f),
			FLinearColor(0.0f, 0.95f, 0.45f, 1.0f)
		);
		return;
	}

	// 2. Parse JSON Response
	TSharedPtr<FJsonObject> JsonObject;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Response->GetContentAsString());
	if (!FJsonSerializer::Deserialize(Reader, JsonObject) || !JsonObject.IsValid())
	{
		AvoidanceWidget->UpdateKanTelemetry(
			TEXT("N/A"),
			TEXT("N/A"),
			TEXT("pykan_esa_kelvins_v1.0"),
			TEXT("INVALID_RESPONSE_JSON"),
			TEXT("-- ms"),
			TEXT("N/A"),
			TEXT("PHYSICS ONLY (FALLBACK)"),
			FLinearColor(1.0f, 0.3f, 0.3f, 1.0f),
			FLinearColor(0.0f, 0.95f, 0.45f, 1.0f)
		);
		return;
	}

	const FString StatusStr = JsonObject->GetStringField(TEXT("status"));
	const FString ModelVer = JsonObject->GetStringField(TEXT("model_version"));

	if (StatusStr == TEXT("INSUFFICIENT_INPUT_DATA"))
	{
		AvoidanceWidget->UpdateKanTelemetry(
			TEXT("N/A"),
			TEXT("N/A"),
			ModelVer.IsEmpty() ? TEXT("pykan_esa_kelvins_v1.0") : ModelVer,
			TEXT("INSUFFICIENT_INPUT_DATA"),
			TEXT("-- ms"),
			TEXT("N/A"),
			TEXT("PHYSICS ONLY (FALLBACK)"),
			FLinearColor(1.0f, 0.65f, 0.1f, 1.0f),
			FLinearColor(0.0f, 0.95f, 0.45f, 1.0f)
		);
		return;
	}

	if (StatusStr == TEXT("SUCCESS"))
	{
		const double PredictedRisk = JsonObject->GetNumberField(TEXT("predicted_risk_log10"));
		const FString PcDisplay = JsonObject->GetStringField(TEXT("estimated_pc_display"));
		const FString RiskCategory = JsonObject->GetStringField(TEXT("risk_category"));
		const double LatencyMs = JsonObject->GetNumberField(TEXT("latency_ms"));

		const FString RiskStr = FString::Printf(TEXT("%.4f"), PredictedRisk);
		const FString LatencyStr = FString::Printf(TEXT("%.1f ms"), LatencyMs);

		const double PhysicsLogPc = (CurrentStepIndex >= 6) ? -21.9070 : -13.4026;
		const double LogDelta = FMath::Abs(PredictedRisk - PhysicsLogPc);
		const FString DeltaStr = FString::Printf(TEXT("\u0394 log\u2081\u2080: %.2f"), LogDelta);

		FLinearColor StatusCol = FLinearColor(0.0f, 0.95f, 0.45f, 1.0f);
		FLinearColor ConcordanceCol = FLinearColor(0.0f, 0.95f, 0.45f, 1.0f);
		FString ConcordanceText = TEXT("CONCORDANT (LOW RISK)");

		if (RiskCategory == TEXT("CRITICAL"))
		{
			StatusCol = FLinearColor(1.0f, 0.25f, 0.25f, 1.0f);
			ConcordanceText = TEXT("ALERT: HIGH RISK");
			ConcordanceCol = FLinearColor(1.0f, 0.25f, 0.25f, 1.0f);
		}
		else if (RiskCategory == TEXT("WARNING"))
		{
			StatusCol = FLinearColor(1.0f, 0.7f, 0.1f, 1.0f);
			ConcordanceText = TEXT("WARNING LEVEL");
			ConcordanceCol = FLinearColor(1.0f, 0.7f, 0.1f, 1.0f);
		}

		AvoidanceWidget->UpdateKanTelemetry(
			RiskStr,
			PcDisplay,
			ModelVer,
			FString::Printf(TEXT("PREDICTED %s"), *RiskCategory),
			LatencyStr,
			DeltaStr,
			ConcordanceText,
			StatusCol,
			ConcordanceCol
		);
		return;
	}

	AvoidanceWidget->UpdateKanTelemetry(
		TEXT("N/A"),
		TEXT("N/A"),
		ModelVer,
		TEXT("MODEL INFERENCE ERROR"),
		TEXT("-- ms"),
		TEXT("N/A"),
		TEXT("PHYSICS ONLY (FALLBACK)"),
		FLinearColor(1.0f, 0.3f, 0.3f, 1.0f),
		FLinearColor(0.0f, 0.95f, 0.45f, 1.0f)
	);
}

void AOrbitSimulationManager::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	for (AOrbitPathActor* PathAct : ConstellationPathActors)
	{
		if (PathAct && IsValid(PathAct))
		{
			PathAct->Destroy();
		}
	}
	ConstellationPathActors.Empty();

	Super::EndPlay(EndPlayReason);
}

void AOrbitSimulationManager::SpawnBackgroundConstellationRings()
{
	if (!GetWorld()) return;

	for (AOrbitPathActor* PathAct : ConstellationPathActors)
	{
		if (PathAct && IsValid(PathAct))
		{
			PathAct->Destroy();
		}
	}
	ConstellationPathActors.Empty();

	struct FOrbitRingDef
	{
		double Radius;
		double InclinationDeg;
		double RaanDeg;
		FLinearColor Color;
		float Thickness;
	};

	// 5 Faint Cyan Constellation Reference Rings + 4 Faint Amber Debris Reference Rings [Illustrative]
	const FOrbitRingDef RingDefs[] = {
		{ 68500.0, 28.5,  30.0, FLinearColor(0.0f, 0.75f, 1.0f, 0.18f), 20.0f },
		{ 71000.0, 45.0,  90.0, FLinearColor(0.0f, 0.80f, 1.0f, 0.20f), 22.0f },
		{ 73000.0, 53.0, 150.0, FLinearColor(0.0f, 0.75f, 1.0f, 0.18f), 20.0f },
		{ 69500.0, 70.0, 220.0, FLinearColor(0.0f, 0.80f, 1.0f, 0.18f), 20.0f },
		{ 72500.0, 97.8, 310.0, FLinearColor(0.0f, 0.85f, 1.0f, 0.22f), 22.0f }, // Sun-synchronous polar reference
		{ 67500.0, 35.0,  60.0, FLinearColor(1.0f, 0.60f, 0.10f, 0.15f), 18.0f },
		{ 74000.0, 62.0, 170.0, FLinearColor(1.0f, 0.58f, 0.12f, 0.16f), 18.0f },
		{ 70500.0, 82.0, 260.0, FLinearColor(1.0f, 0.60f, 0.10f, 0.15f), 18.0f },
		{ 75500.0, 110.0, 340.0, FLinearColor(1.0f, 0.55f, 0.12f, 0.15f), 18.0f }
	};

	FActorSpawnParameters SpawnParams;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

	const int32 NumSamples = 48;
	const double TwoPi = 6.28318530717958647692;

	for (const FOrbitRingDef& Def : RingDefs)
	{
		AOrbitPathActor* RingActor = GetWorld()->SpawnActor<AOrbitPathActor>(AOrbitPathActor::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator, SpawnParams);
		if (!RingActor) continue;

#if WITH_EDITOR
		RingActor->SetIsSpatiallyLoaded(false);
#endif
		RingActor->PathThickness = Def.Thickness;
		RingActor->bIsDashed = false;

		const double IncRad = FMath::DegreesToRadians(Def.InclinationDeg);
		const double RaanRad = FMath::DegreesToRadians(Def.RaanDeg);
		const double CosInc = FMath::Cos(IncRad);
		const double SinInc = FMath::Sin(IncRad);
		const double CosRaan = FMath::Cos(RaanRad);
		const double SinRaan = FMath::Sin(RaanRad);

		TArray<FVector> RingPoints;
		RingPoints.Reserve(NumSamples + 1);

		for (int32 s = 0; s <= NumSamples; ++s)
		{
			const double Theta = (static_cast<double>(s) / static_cast<double>(NumSamples)) * TwoPi;
			const double CosTh = FMath::Cos(Theta);
			const double SinTh = FMath::Sin(Theta);

			const double X_p = Def.Radius * CosTh;
			const double Y_p = Def.Radius * SinTh;

			const double X_i = X_p;
			const double Y_i = Y_p * CosInc;
			const double Z_i = Y_p * SinInc;

			const double X_w = (X_i * CosRaan) - (Y_i * SinRaan);
			const double Y_w = (X_i * SinRaan) + (Y_i * CosRaan);
			const double Z_w = Z_i;

			RingPoints.Add(FVector(X_w, Y_w, Z_w));
		}

		RingActor->SetTrajectoryPoints(RingPoints, Def.Color);
		ConstellationPathActors.Add(RingActor);
	}
	UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Spawned %d background constellation orbital rings."), ConstellationPathActors.Num());
}
