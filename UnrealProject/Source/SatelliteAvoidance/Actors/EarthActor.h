// EarthActor.h - Earth Sphere & Atmosphere Actor in UE5
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EarthActor.generated.h"

UCLASS()
class SATELLITEAVOIDANCE_API AEarthActor : public AActor
{
	GENERATED_BODY()

public:
	AEarthActor();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* EarthMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* AtmosphereMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* StarfieldMesh;

	/** Scientific physical Earth radius in Unreal Units (default: 63,781.37 uu at scale 0.01). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Earth Properties")
	double EarthRadiusUe = 63781.37;

	/** Visual Earth radius for aesthetic mission-control framing (default: 26,000 uu).
	 * Fills ~42% of the orbital viewport with majestic planetary curvature inside the 70,000 uu orbit. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Earth Properties")
	double VisualEarthRadiusUe = 26000.0;

	/** Atmosphere radius multiplier relative to Earth (default: 1.035, ~910 uu luminous rim). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Earth Properties")
	double AtmosphereScaleMultiplier = 1.035;

	/** Rotational speed in degrees per simulation second (Earth sidereal rotation). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Earth Properties")
	double RotationRateDegPerSec = 360.0 / 86164.09;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Earth Materials")
	UMaterialInterface* EarthMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Earth Materials")
	UMaterialInterface* AtmosphereMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Earth Materials")
	UMaterialInterface* StarfieldMaterial;

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaTime) override;

	void ApplyEarthMaterials();
};
