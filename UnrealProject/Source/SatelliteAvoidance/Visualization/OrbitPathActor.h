// OrbitPathActor.h - Renders sampled orbital trajectory polylines in UE5
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Components/SplineComponent.h"
#include "Components/SplineMeshComponent.h"
#include "OrbitPathActor.generated.h"

UCLASS()
class SATELLITEAVOIDANCE_API AOrbitPathActor : public AActor
{
	GENERATED_BODY()

public:
	AOrbitPathActor();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	USplineComponent* TrajectorySpline;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Visuals")
	FLinearColor PathColor = FLinearColor(0.0f, 0.85f, 1.0f, 1.0f); // Default Cyan

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Visuals")
	float PathThickness = 3.5f; // Sleek, crisp orbital trajectory ribbon width

	UPROPERTY()
	TArray<USplineMeshComponent*> SplineMeshes;

	virtual void OnConstruction(const FTransform& Transform) override;

	UFUNCTION(BlueprintCallable, Category = "Trajectory")
	void SetTrajectoryPoints(const TArray<FVector>& Points, const FLinearColor& InColor);

	virtual void SetActorHiddenInGame(bool bNewHiddenInGame) override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	void ClearSplineMeshes();
	void BuildSplineMeshGeometry();
};
