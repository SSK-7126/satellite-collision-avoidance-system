// CoordinateAdapter.cpp
#include "CoordinateAdapter.h"

FVector UCoordinateAdapter::EciToUnrealPosition(const FVector& EciPositionMetres, double ScaleFactor)
{
	return FVector(
		EciPositionMetres.X * ScaleFactor,
		-EciPositionMetres.Y * ScaleFactor, // Invert Y for right-handed to left-handed conversion
		EciPositionMetres.Z * ScaleFactor
	);
}

FVector UCoordinateAdapter::UnrealToEciPosition(const FVector& UnrealPositionUnits, double ScaleFactor)
{
	const double SafeScale = (ScaleFactor > 0.0) ? ScaleFactor : DefaultRenderScale;
	return FVector(
		UnrealPositionUnits.X / SafeScale,
		-UnrealPositionUnits.Y / SafeScale,
		UnrealPositionUnits.Z / SafeScale
	);
}

FVector UCoordinateAdapter::EciToUnrealVelocity(const FVector& EciVelocityMps, double ScaleFactor)
{
	return FVector(
		EciVelocityMps.X * ScaleFactor,
		-EciVelocityMps.Y * ScaleFactor,
		EciVelocityMps.Z * ScaleFactor
	);
}

FRotator UCoordinateAdapter::CalculateFlightOrientation(const FVector& UnrealVelocity)
{
	if (UnrealVelocity.IsNearlyZero(1e-4))
	{
		return FRotator::ZeroRotator;
	}

	const double HorizSpeed = FMath::Sqrt(UnrealVelocity.X * UnrealVelocity.X + UnrealVelocity.Y * UnrealVelocity.Y);
	const double YawDeg = FMath::RadiansToDegrees(FMath::Atan2(UnrealVelocity.Y, UnrealVelocity.X));
	const double PitchDeg = FMath::RadiansToDegrees(FMath::Atan2(UnrealVelocity.Z, FMath::Max(HorizSpeed, 1e-6)));

	return FRotator(PitchDeg, YawDeg, 0.0);
}

