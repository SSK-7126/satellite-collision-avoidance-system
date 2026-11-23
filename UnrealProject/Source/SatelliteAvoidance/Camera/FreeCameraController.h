// FreeCameraController.h - Dedicated 3D Orbital Free Camera Controller in UE5
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Camera/CameraComponent.h"
#include "FreeCameraController.generated.h"

UENUM(BlueprintType)
enum class EOrbitCameraMode : uint8
{
	FreeCamera UMETA(DisplayName = "Free Camera"),
	PresetCamera UMETA(DisplayName = "Preset Camera")
};

UCLASS()
class SATELLITEAVOIDANCE_API AFreeCameraController : public AActor
{
	GENERATED_BODY()

public:
	AFreeCameraController();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
	USceneComponent* TransformRoot;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
	UCameraComponent* CameraComponent;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera Mode")
	EOrbitCameraMode ActiveMode = EOrbitCameraMode::FreeCamera;

	/** The 3D world position the camera orbits around and looks at. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera Navigation")
	FVector FocusTarget = FVector(0.0f, 0.0f, 0.0f);

	/** Desired distance to the focus target in Unreal Units. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera Navigation")
	double TargetDistance = 3500.0;

	/** Current smoothly interpolated distance. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera Navigation")
	double CurrentDistance = 3500.0;

	/** Orbit angles: Pitch (elevation -85 to +85), Yaw (azimuth 0 to 360), Roll (0). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera Navigation")
	FRotator OrbitRotation = FRotator(-12.0f, 160.0f, 0.0f);

	/** Current target pitch and yaw for smooth mouse orbit interpolation. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera Navigation")
	FRotator DesiredRotation = FRotator(-12.0f, 160.0f, 0.0f);

	/** Currently selected object (Earth, Satellite, Debris) for focus/tracking. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera Navigation")
	AActor* SelectedActor = nullptr;

	/** Default mission-control framing values for quick reset. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Default Framing")
	FVector DefaultFocusTarget = FVector(0.0f, 0.0f, 0.0f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Default Framing")
	FRotator DefaultOrbitRotation = FRotator(-12.0f, 160.0f, 0.0f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Default Framing")
	double DefaultDistance = 3500.0;

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaTime) override;

	/** Orbit the camera around focus target by mouse drag delta. */
	UFUNCTION(BlueprintCallable, Category = "Camera Navigation")
	void AddOrbitInput(float DeltaPitch, float DeltaYaw);

	/** Pan the camera viewing target horizontally/vertically. */
	UFUNCTION(BlueprintCallable, Category = "Camera Navigation")
	void AddPanInput(float DeltaRight, float DeltaUp);

	/** Zoom camera distance by mouse wheel delta. */
	UFUNCTION(BlueprintCallable, Category = "Camera Navigation")
	void AddZoomInput(float WheelDelta);

	/** Focus camera smoothly on selected object or designated actor. */
	UFUNCTION(BlueprintCallable, Category = "Camera Navigation")
	void FocusOnActor(AActor* InActor);

	/** Frame the currently selected actor with appropriate distance. */
	UFUNCTION(BlueprintCallable, Category = "Camera Navigation")
	void FrameSelected();

	/** Reset camera to the default Mission Control overview framing. */
	UFUNCTION(BlueprintCallable, Category = "Camera Navigation")
	void ResetToDefault();

	/** Seamlessly activate free camera taking over from any active view. */
	UFUNCTION(BlueprintCallable, Category = "Camera Navigation")
	void ActivateFreeCamera(const FVector& FromLocation, const FRotator& FromRotation);

	/** Check if free camera mode is currently active. */
	UFUNCTION(BlueprintCallable, Category = "Camera Mode")
	bool IsFreeCameraActive() const { return ActiveMode == EOrbitCameraMode::FreeCamera; }

	/** Set active camera mode. */
	UFUNCTION(BlueprintCallable, Category = "Camera Mode")
	void SetCameraMode(EOrbitCameraMode NewMode) { ActiveMode = NewMode; }

	/** Store custom default framing parameters. */
	void ConfigureDefaultFraming(const FVector& InFocus, const FRotator& InRot, double InDist);
};
