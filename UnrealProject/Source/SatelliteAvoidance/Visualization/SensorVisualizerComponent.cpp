// SensorVisualizerComponent.cpp
#include "SensorVisualizerComponent.h"
#include "DrawDebugHelpers.h"

USensorVisualizerComponent::USensorVisualizerComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	bAutoActivate = true;
}

void USensorVisualizerComponent::UpdateTrackingState(const FVector& TargetPosUe, bool bInTargetVisible, const FString& Status)
{
	CurrentTargetPositionUe = TargetPosUe;
	bTargetInFov = bInTargetVisible;
	bIsTracking = bInTargetVisible;
	TrackingStatus = Status;

	if (bInTargetVisible && GetWorld())
	{
		RenderObservationRay(2.0f);
	}
}

void USensorVisualizerComponent::RenderObservationRay(float LineThickness)
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	const FVector SensorPos = GetComponentLocation();
	const FVector RayDir = (CurrentTargetPositionUe - SensorPos).GetSafeNormal();
	const double Dist = FVector::Dist(SensorPos, CurrentTargetPositionUe);

	if (Dist > 0.0 && Dist <= MaxRangeUe)
	{
		// Draw cyan observation ray
		const FColor RayColor = bTargetInFov ? FColor(0, 220, 255, 200) : FColor(255, 120, 0, 150);
		DrawDebugLine(World, SensorPos, CurrentTargetPositionUe, RayColor, false, -1.0f, 0, LineThickness);
	}
}
