// CoordinateAdapter.h - ECI to Unreal Engine Coordinate Transformation
#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "CoordinateAdapter.generated.h"

/**
 * Coordinate Conversion Adapter between Earth-Centred Inertial (ECI)
 * and Unreal Engine 5 Coordinate Space.
 * Follows Section 2 of the Satellite Anti-Collision Technical Guide.
 */
UCLASS()
class SATELLITEAVOIDANCE_API UCoordinateAdapter : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	// Default macro display scale: 1 uu = 100 metres (0.01 uu/m)
	static constexpr double DefaultRenderScale = 0.01;

	/**
	 * Convert 3D position vector from right-handed ECI (metres) to left-handed Unreal Engine (uu).
	 * X_ue = +X_eci * Scale
	 * Y_ue = -Y_eci * Scale   (handedness reflection)
	 * Z_ue = +Z_eci * Scale
	 */
	UFUNCTION(BlueprintPure, Category = "Astrodynamics|Coordinates")
	static FVector EciToUnrealPosition(const FVector& EciPositionMetres, double ScaleFactor = 0.01);

	/**
	 * Inverse transform: Convert Unreal Engine position (uu) back to ECI metres.
	 */
	UFUNCTION(BlueprintPure, Category = "Astrodynamics|Coordinates")
	static FVector UnrealToEciPosition(const FVector& UnrealPositionUnits, double ScaleFactor = 0.01);

	/**
	 * Convert 3D velocity vector from ECI (m/s) to Unreal Engine (uu/s).
	 */
	UFUNCTION(BlueprintPure, Category = "Astrodynamics|Coordinates")
	static FVector EciToUnrealVelocity(const FVector& EciVelocityMps, double ScaleFactor = 0.01);

	/**
	 * Calculate velocity-aligned flight orientation (along-track attitude) in Unreal Engine.
	 * Pitch: Elevation above X-Y plane
	 * Yaw: Azimuth in X-Y plane
	 * Roll: 0.0 deg baseline
	 */
	UFUNCTION(BlueprintPure, Category = "Astrodynamics|Coordinates")
	static FRotator CalculateFlightOrientation(const FVector& UnrealVelocity);
};

