// SensorVisualizerComponent.h - Sensor FOV and observation ray visualizer component
#pragma once

#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "SensorVisualizerComponent.generated.h"

/**
 * Visualizes sensor field-of-view (FOV), observation line-of-sight rays,
 * and tracking coverage in Unreal Engine.
 * Follows Section 8 and Section 9 of the Satellite Anti-Collision Technical Guide.
 */
UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class SATELLITEAVOIDANCE_API USensorVisualizerComponent : public USceneComponent
{
	GENERATED_BODY()

public:
	USensorVisualizerComponent();

	// Sensor FOV half-angle in degrees
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Sensor Visualization")
	double FieldOfViewDeg = 30.0;

	// Maximum visual range in Unreal Units
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Sensor Visualization")
	double MaxRangeUe = 2000.0;

	// Whether the sensor is currently tracking a target
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Sensor Visualization")
	bool bIsTracking = false;

	// Whether target is inside the sensor FOV and visible
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Sensor Visualization")
	bool bTargetInFov = false;

	// Sensor modality label (e.g. "OPTICAL_LOS", "RADAR_DOPPLER", "ONBOARD_GNSS")
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Sensor Visualization")
	FString SensorTypeLabel = TEXT("OPTICAL_LOS");

	// Current operational status
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Sensor Visualization")
	FString TrackingStatus = TEXT("ACTIVE_STANDBY");

	// Latest target position in Unreal space
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Sensor Visualization")
	FVector CurrentTargetPositionUe = FVector::ZeroVector;

	/**
	 * Update sensor tracking state and observation ray to the target.
	 */
	UFUNCTION(BlueprintCallable, Category = "Sensor Visualization")
	void UpdateTrackingState(const FVector& TargetPosUe, bool bInTargetVisible, const FString& Status);

	/**
	 * Draw observation line-of-sight ray and FOV boundary.
	 */
	UFUNCTION(BlueprintCallable, Category = "Sensor Visualization")
	void RenderObservationRay(float LineThickness = 2.0f);
};
