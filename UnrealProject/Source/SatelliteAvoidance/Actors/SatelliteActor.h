// SatelliteActor.h - Protected Primary Satellite in UE5
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SatelliteActor.generated.h"

UENUM(BlueprintType)
enum class ESatelliteVisualState : uint8
{
	NominalFlight UMETA(DisplayName = "Nominal Flight"),
	ConjunctionAlert UMETA(DisplayName = "Conjunction Alert"),
	ManoeuvredFlight UMETA(DisplayName = "Manoeuvred Flight")
};

UCLASS()
class SATELLITEAVOIDANCE_API ASatelliteActor : public AActor
{
	GENERATED_BODY()

public:
	ASatelliteActor();

	// Central Bus (Golden metallic cuboid)
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* SatelliteBody;

	// Inboard Left Solar Panel
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* SolarPanelLeft;

	// Outboard Left Solar Panel (Segmented)
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* SolarPanelLeft_Outboard;

	// Left Solar Panel Yoke Boom
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* SolarYokeLeft;

	// Inboard Right Solar Panel
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* SolarPanelRight;

	// Outboard Right Solar Panel (Segmented)
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* SolarPanelRight_Outboard;

	// Right Solar Panel Yoke Boom
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* SolarYokeRight;

	// Communications Antenna Mast
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* AntennaMast;

	// Communications High-Gain Dish Antenna
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* AntennaDish;

	// Instrument / Sensor Payload Deck
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* PayloadDeck;

	// Earth-facing Optical Sensor Aperture
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* EarthSensor;

	// Main Propulsion Engine / Thruster Nozzle
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	UStaticMeshComponent* ThrusterNozzle;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Satellite Properties")
	FString SatelliteId = TEXT("PROTECTED_SAT");

	UPROPERTY(BlueprintReadOnly, Category = "Satellite State")
	ESatelliteVisualState CurrentState = ESatelliteVisualState::NominalFlight;

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void BeginPlay() override;

	UFUNCTION(BlueprintCallable, Category = "Satellite State")
	void SetVisualState(ESatelliteVisualState NewState);

	void ApplySatelliteMaterials();
};
