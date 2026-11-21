// ManoeuvreVisualizer.h - Renders burn location marker and delta-v vector arrow in UE5
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ManoeuvreVisualizer.generated.h"

UCLASS()
class SATELLITEAVOIDANCE_API AManoeuvreVisualizer : public AActor
{
	GENERATED_BODY()

public:
	AManoeuvreVisualizer();

	// Burn Location Ring Indicator
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* BurnMarkerRing;

	// Delta-V Vector Arrow Shaft
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* DeltaVArrowShaft;

	// Delta-V Vector Arrow Cone Tip
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* DeltaVArrow;

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void BeginPlay() override;

	UFUNCTION(BlueprintCallable, Category = "Manoeuvre Visuals")
	void SetManoeuvreGeometry(const FVector& BurnLocationUe, const FVector& DeltaVVectorUe, double DeltaVMagnitudeMps);

	void ApplyVisualizerMaterials();
};
