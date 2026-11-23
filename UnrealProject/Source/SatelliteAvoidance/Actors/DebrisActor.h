// DebrisActor.h - Secondary Debris Object in UE5
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "DebrisActor.generated.h"

UCLASS()
class SATELLITEAVOIDANCE_API ADebrisActor : public AActor
{
	GENERATED_BODY()

public:
	ADebrisActor();

	// Scene Root representing exact scientific center
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	USceneComponent* SceneRoot;

	// Visual Root holding all meshes for independent scaling
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	USceneComponent* VisualRoot;

	// Independent visual scale factor for debris meshes (prominently visible without altering scientific coordinates)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Visual Scaling")
	float VisualMeshScale = 18.0f;

	// Primary irregular jagged fragment core
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* DebrisMesh;

	// Angular secondary shearing shard A
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* FragmentShardA;

	// Angular secondary shearing shard B
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* FragmentShardB;

	// Sheared structural truss/tube protruding from fragment
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* TornStrut;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Debris Properties")
	FString DebrisId = TEXT("DEBRIS_B");

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void BeginPlay() override;

	void ApplyDebrisMaterials();
};
