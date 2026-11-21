// ConjunctionVisualizer.h - Renders TCA markers, miss distance connector, and encounter plane
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ConjunctionVisualizer.generated.h"

UCLASS()
class SATELLITEAVOIDANCE_API AConjunctionVisualizer : public AActor
{
	GENERATED_BODY()

public:
	AConjunctionVisualizer();

	// Primary Satellite TCA Marker Sphere
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* TcaMarkerSphere;

	// Secondary Debris TCA Marker Sphere
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* DebrisTcaMarkerSphere;

	// Miss-Distance Connector Line (Cylinder between Satellite and Debris at TCA)
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* MissDistanceLine;

	// Encounter / B-Plane Reference Disc
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* EncounterPlaneDisc;

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void BeginPlay() override;

	UFUNCTION(BlueprintCallable, Category = "Conjunction Visuals")
	void UpdateConjunctionGeometry(const FVector& SatTcaPos, const FVector& DebrisTcaPos, double MissDistanceUe);

	void ApplyVisualizerMaterials();
};
