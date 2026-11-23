// FreeCameraController.cpp
#include "FreeCameraController.h"
#include "Kismet/KismetMathLibrary.h"

AFreeCameraController::AFreeCameraController()
{
	PrimaryActorTick.bCanEverTick = true;

	TransformRoot = CreateDefaultSubobject<USceneComponent>(TEXT("TransformRoot"));
	RootComponent = TransformRoot;

	CameraComponent = CreateDefaultSubobject<UCameraComponent>(TEXT("CameraComponent"));
	CameraComponent->SetupAttachment(RootComponent);
	CameraComponent->SetFieldOfView(52.0f);
	CameraComponent->bConstrainAspectRatio = false;

	// Calibrated orbital vantage: elevated orbital overview framing Earth in background, Satellite foreground left, Debris right
	FocusTarget = FVector(23800.0f, -14900.0f, 0.0f);
	TargetDistance = 97082.0;
	CurrentDistance = 97082.0;
	OrbitRotation = FRotator(-18.0f, 159.0f, 0.0f);
	DesiredRotation = OrbitRotation;

	DefaultFocusTarget = FocusTarget;
	DefaultOrbitRotation = OrbitRotation;
	DefaultDistance = TargetDistance;
}

void AFreeCameraController::BeginPlay()
{
	Super::BeginPlay();
#if WITH_EDITOR
	SetIsSpatiallyLoaded(false);
#endif
	CurrentDistance = TargetDistance;
	OrbitRotation = DesiredRotation;
}

void AFreeCameraController::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	if (ActiveMode != EOrbitCameraMode::FreeCamera)
	{
		return;
	}

	// Smoothly follow selected actor if one is actively selected
	if (SelectedActor && IsValid(SelectedActor))
	{
		FocusTarget = FMath::VInterpTo(FocusTarget, SelectedActor->GetActorLocation(), DeltaTime, 4.0f);
	}

	// Smooth interpolation for distance and rotation
	CurrentDistance = FMath::FInterpTo(CurrentDistance, TargetDistance, DeltaTime, 8.0f);
	OrbitRotation = FMath::RInterpTo(OrbitRotation, DesiredRotation, DeltaTime, 12.0f);

	// Compute world camera placement looking at FocusTarget
	const FVector LookDirection = OrbitRotation.Vector();
	const FVector NewLocation = FocusTarget - (LookDirection * CurrentDistance);

	SetActorLocationAndRotation(NewLocation, OrbitRotation);
}

void AFreeCameraController::AddOrbitInput(float DeltaPitch, float DeltaYaw)
{
	// Mouse orbit: Left click + drag
	DesiredRotation.Pitch = FMath::Clamp(DesiredRotation.Pitch + DeltaPitch, -85.0f, 85.0f);
	DesiredRotation.Yaw = FRotator::NormalizeAxis(DesiredRotation.Yaw + DeltaYaw);
}

void AFreeCameraController::AddPanInput(float DeltaRight, float DeltaUp)
{
	// Mouse pan: Right click + drag
	// Pan speed scales proportionally with distance to focus point
	const float PanScale = FMath::Max(1.0f, static_cast<float>(CurrentDistance) * 0.0012f);

	const FRotationMatrix CamMatrix(OrbitRotation);
	const FVector CamRight = CamMatrix.GetScaledAxis(EAxis::Y);
	const FVector CamUp = CamMatrix.GetScaledAxis(EAxis::Z);

	FocusTarget += (CamRight * DeltaRight * PanScale) + (CamUp * DeltaUp * PanScale);

	// If user manually pans, detach tracking from selected actor
	SelectedActor = nullptr;
}

void AFreeCameraController::AddZoomInput(float WheelDelta)
{
	// Mouse zoom: Scroll wheel
	const double ZoomFactor = 0.12;
	TargetDistance = FMath::Clamp(TargetDistance * (1.0 - (WheelDelta * ZoomFactor)), 500.0, 500000.0);
}

void AFreeCameraController::FocusOnActor(AActor* InActor)
{
	if (!InActor) return;

	SelectedActor = InActor;
	FocusTarget = InActor->GetActorLocation();

	// Optimal framing distance based on enlarged visual mesh scaling
	const FString ActorName = InActor->GetName();
	if (ActorName.Contains(TEXT("Earth"), ESearchCase::IgnoreCase))
	{
		TargetDistance = 55000.0;
		DesiredRotation = FRotator(-10.0f, 155.0f, 0.0f);
	}
	else if (ActorName.Contains(TEXT("Debris"), ESearchCase::IgnoreCase))
	{
		TargetDistance = 7500.0;
		DesiredRotation = FRotator(-15.0f, 75.0f, 0.0f);
	}
	else
	{
		TargetDistance = 14000.0;
		DesiredRotation = FRotator(-12.0f, 150.0f, 0.0f);
	}
	OrbitRotation = DesiredRotation;
	CurrentDistance = TargetDistance;

	const FVector LookDirection = OrbitRotation.Vector();
	const FVector NewLocation = FocusTarget - (LookDirection * CurrentDistance);
	SetActorLocationAndRotation(NewLocation, OrbitRotation);
}

void AFreeCameraController::FrameSelected()
{
	if (SelectedActor)
	{
		FocusOnActor(SelectedActor);
	}
	else
	{
		ResetToDefault();
	}
}

void AFreeCameraController::ResetToDefault()
{
	SelectedActor = nullptr;
	FocusTarget = DefaultFocusTarget;
	DesiredRotation = DefaultOrbitRotation;
	OrbitRotation = DefaultOrbitRotation;
	TargetDistance = DefaultDistance;
	CurrentDistance = DefaultDistance;

	const FVector LookDirection = OrbitRotation.Vector();
	const FVector NewLocation = FocusTarget - (LookDirection * CurrentDistance);
	SetActorLocationAndRotation(NewLocation, OrbitRotation);
}

void AFreeCameraController::ConfigureDefaultFraming(const FVector& InFocus, const FRotator& InRot, double InDist)
{
	DefaultFocusTarget = InFocus;
	DefaultOrbitRotation = InRot;
	DefaultDistance = InDist;

	FocusTarget = InFocus;
	DesiredRotation = InRot;
	OrbitRotation = InRot;
	TargetDistance = InDist;
	CurrentDistance = InDist;

	const FVector LookDirection = OrbitRotation.Vector();
	const FVector NewLocation = FocusTarget - (LookDirection * CurrentDistance);
	SetActorLocationAndRotation(NewLocation, OrbitRotation);
}

void AFreeCameraController::ActivateFreeCamera(const FVector& FromLocation, const FRotator& FromRotation)
{
	ActiveMode = EOrbitCameraMode::FreeCamera;
	SelectedActor = nullptr;

	// Seamless handoff: compute focus point along current line of sight
	const double HandoffDistance = FMath::Clamp(TargetDistance, 500.0, 20000.0);
	FocusTarget = FromLocation + (FromRotation.Vector() * HandoffDistance);
	DesiredRotation = FromRotation;
	OrbitRotation = FromRotation;
	TargetDistance = HandoffDistance;
	CurrentDistance = HandoffDistance;

	SetActorLocationAndRotation(FromLocation, FromRotation);
}
