// OrbitSimulationManager.cpp
#include "OrbitSimulationManager.h"
#include "SatelliteAvoidance/DataBridge/CoordinateAdapter.h"
#include "Kismet/GameplayStatics.h"
#include "GameFramework/PlayerController.h"
#include "Camera/CameraActor.h"
#include "EngineUtils.h"

AOrbitSimulationManager::AOrbitSimulationManager()
{
	PrimaryActorTick.bCanEverTick = true;
	DataBridge = CreateDefaultSubobject<USimulationDataBridge>(TEXT("DataBridge"));
	CurrentStepIndex = 1;
	CurrentSimulationTime = 0.0;
	TimeDilation = 5.0;
	bIsPlaying = true;
	bManoeuvreExecuted = false;
}

void AOrbitSimulationManager::BeginPlay()
{
	Super::BeginPlay();

	// Default relative path to the generated Python payload
	const FString DefaultPayloadPath = FPaths::ProjectDir() / TEXT("../D2/visualization/unreal_simulation_payload.json");
	InitializeSimulationFromPayload(DefaultPayloadPath);

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
		if (!SatNominalPathActor || !DebrisPathActor || !SatModifiedPathActor)
		{
			for (TActorIterator<AOrbitPathActor> It(GetWorld()); It; ++It)
			{
				const FString Label = It->GetActorLabel();
				if (Label.Contains(TEXT("Debris")))
				{
					DebrisPathActor = *It;
				}
				else if (Label.Contains(TEXT("Modified")))
				{
					SatModifiedPathActor = *It;
				}
				else if (!SatNominalPathActor)
				{
					SatNominalPathActor = *It;
				}
			}
		}

		// Auto-discover CameraActors in scene
		CameraViews.Empty();
		for (TActorIterator<ACameraActor> It(GetWorld()); It; ++It)
		{
			CameraViews.Add(*It);
		}
		if (CameraViews.Num() > 0 && !OverviewCamera)
		{
			for (AActor* Cam : CameraViews)
			{
				if (Cam && Cam->GetActorLabel().Contains(TEXT("Earth_Overview"), ESearchCase::IgnoreCase))
				{
					OverviewCamera = Cam;
					break;
				}
			}
			if (!OverviewCamera)
			{
				OverviewCamera = CameraViews[0];
			}
		}
	}

	// Instantiate and display Telemetry HUD in Play In Editor / Runtime
	if (GetWorld() && (GetWorld()->IsGameWorld() || GetWorld()->IsPlayInEditor()))
	{
		AvoidanceWidget = CreateWidget<UAvoidanceInfoPanelWidget>(GetWorld(), UAvoidanceInfoPanelWidget::StaticClass());
		if (AvoidanceWidget)
		{
			AvoidanceWidget->AddToViewport(100);
			AvoidanceWidget->UpdatePlaybackControls(bIsPlaying, TimeDilation, CurrentStepIndex, DataBridge ? DataBridge->DemonstrationSequence.Num() : 8);
			UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Telemetry HUD widget added to viewport."));
		}

		// Set initial camera view
		if (OverviewCamera)
		{
			APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
			if (PC)
			{
				PC->SetViewTarget(OverviewCamera);
				UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: View target set to OverviewCamera."));
			}
		}

		// Setup interactive player keyboard controls
		SetupPlayerInput();
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

	// R: Reset simulation
	InputComponent->BindKey(EKeys::R, IE_Pressed, this, &AOrbitSimulationManager::ResetSimulation);

	// C: Cycle Camera View
	InputComponent->BindKey(EKeys::C, IE_Pressed, this, &AOrbitSimulationManager::CycleCameraView);

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

	// Initialize Orbit Paths with visible spline geometry
	if (SatNominalPathActor && DataBridge->SatNominalPositions.Num() > 0)
	{
		SatNominalPathActor->SetTrajectoryPoints(DataBridge->SatNominalPositions, FLinearColor(0.0f, 0.85f, 1.0f, 1.0f)); // Cyan
	}

	if (DebrisPathActor && DataBridge->DebrisPositions.Num() > 0)
	{
		DebrisPathActor->SetTrajectoryPoints(DataBridge->DebrisPositions, FLinearColor(1.0f, 0.15f, 0.1f, 1.0f)); // Red
	}

	if (SatModifiedPathActor && DataBridge->SatModifiedPositions.Num() > 0)
	{
		SatModifiedPathActor->SetTrajectoryPoints(DataBridge->SatModifiedPositions, FLinearColor(0.15f, 1.0f, 0.35f, 1.0f)); // Vibrant Green
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
		DebrisActor->SetActorLocation(DebPos);
	}

	// Update Telemetry HUD
	if (AvoidanceWidget)
	{
		AvoidanceWidget->UpdateTelemetry(
			CurrentSimulationTime,
			SatelliteActor ? SatelliteActor->SatelliteId : TEXT("CARTOSAT-3"),
			DebrisActor ? DebrisActor->DebrisId : TEXT("DEBRIS_PIECE_99"),
			DataBridge->NominalEncounter,
			DataBridge->PostManoeuvreEncounter,
			DataBridge->SelectedManoeuvre,
			bManoeuvreExecuted
		);
		AvoidanceWidget->UpdatePlaybackControls(bIsPlaying, TimeDilation, CurrentStepIndex, DataBridge->DemonstrationSequence.Num());
	}

	OnTimeUpdated.Broadcast(CurrentSimulationTime);
}

void AOrbitSimulationManager::JumpToStep(int32 StepIndex)
{
	if (!DataBridge || DataBridge->DemonstrationSequence.Num() == 0)
	{
		return;
	}

	CurrentStepIndex = FMath::Clamp(StepIndex, 1, DataBridge->DemonstrationSequence.Num());
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

	if (AvoidanceWidget)
	{
		AvoidanceWidget->CurrentMilestoneHeadline = FString::Printf(TEXT("Step %d / %d: %s"), Step.StepIndex, DataBridge->DemonstrationSequence.Num(), *Step.Headline);
		AvoidanceWidget->UpdatePlaybackControls(bIsPlaying, TimeDilation, CurrentStepIndex, DataBridge->DemonstrationSequence.Num());
	}

	SetCameraForStep(CurrentStepIndex);

	// Update immediately
	Tick(0.0f);
	OnStepTriggered.Broadcast(Step);
	UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Jumped to Step %d (%s) at T+%.1fs"), CurrentStepIndex, *Step.Headline, CurrentSimulationTime);
}

void AOrbitSimulationManager::StepForward()
{
	if (DataBridge && DataBridge->DemonstrationSequence.Num() > 0)
	{
		const int32 NextStep = FMath::Min(CurrentStepIndex + 1, DataBridge->DemonstrationSequence.Num());
		JumpToStep(NextStep);
	}
}

void AOrbitSimulationManager::StepBackward()
{
	const int32 PrevStep = FMath::Max(CurrentStepIndex - 1, 1);
	JumpToStep(PrevStep);
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
	bIsPlaying = true;
	bManoeuvreExecuted = false;

	if (SatModifiedPathActor) { SatModifiedPathActor->SetActorHiddenInGame(true); }
	if (ManoeuvreVisualizer) { ManoeuvreVisualizer->SetActorHiddenInGame(true); }
	if (SatelliteActor) { SatelliteActor->SetVisualState(ESatelliteVisualState::NominalFlight); }

	if (AvoidanceWidget && DataBridge && DataBridge->DemonstrationSequence.Num() > 0)
	{
		AvoidanceWidget->CurrentMilestoneHeadline = FString::Printf(TEXT("Step 1 / %d: %s"), DataBridge->DemonstrationSequence.Num(), *DataBridge->DemonstrationSequence[0].Headline);
		AvoidanceWidget->UpdatePlaybackControls(bIsPlaying, TimeDilation, CurrentStepIndex, DataBridge->DemonstrationSequence.Num());
	}

	SetCameraForStep(1);
	Tick(0.0f);
	UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Simulation reset to initial epoch (T=0.0s)."));
}

void AOrbitSimulationManager::IncreaseSpeed()
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
	SetTimeDilation(SpeedTiers[NumTiers - 1]);
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

	CurrentCameraIndex = (CurrentCameraIndex + 1) % CameraViews.Num();
	AActor* TargetCam = CameraViews[CurrentCameraIndex];
	if (TargetCam)
	{
		APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
		if (PC)
		{
			PC->SetViewTargetWithBlend(TargetCam, 0.75f);
			UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Switched camera to [%s] (Index %d/%d)"), *TargetCam->GetActorLabel(), CurrentCameraIndex + 1, CameraViews.Num());
		}
	}
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

	// 1. Deterministic exact match by actor label
	for (int32 i = 0; i < CameraViews.Num(); ++i)
	{
		if (CameraViews[i] && CameraViews[i]->GetActorLabel().Equals(TargetCameraName, ESearchCase::IgnoreCase))
		{
			CurrentCameraIndex = i;
			APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
			if (PC)
			{
				PC->SetViewTargetWithBlend(CameraViews[i], 0.75f);
			}
			UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Step %d -> Camera [%s] (Index %d/%d)"),
				StepIndex, *TargetCameraName, CurrentCameraIndex + 1, CameraViews.Num());
			return;
		}
	}

	// 2. Fallback: Specific substring match without ambiguous "Overview" collision
	FString CleanTarget = TargetCameraName;
	CleanTarget.RemoveFromStart(TEXT("Camera_"));

	for (int32 i = 0; i < CameraViews.Num(); ++i)
	{
		if (CameraViews[i] && CameraViews[i]->GetActorLabel().Contains(CleanTarget, ESearchCase::IgnoreCase))
		{
			CurrentCameraIndex = i;
			APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
			if (PC)
			{
				PC->SetViewTargetWithBlend(CameraViews[i], 0.75f);
			}
			UE_LOG(LogTemp, Log, TEXT("AOrbitSimulationManager: Step %d -> Camera [%s] via substring [%s] (Index %d/%d)"),
				StepIndex, *CameraViews[i]->GetActorLabel(), *CleanTarget, CurrentCameraIndex + 1, CameraViews.Num());
			return;
		}
	}
}
