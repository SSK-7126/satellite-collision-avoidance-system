// SimulationDataBridge.h - Loads and parses Python JSON simulation payload
#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "SimulationDataBridge.generated.h"

USTRUCT(BlueprintType)
struct FScenarioMetadata
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly)
	FString ScenarioId;

	UPROPERTY(BlueprintReadOnly)
	FString EpochUtc;

	UPROPERTY(BlueprintReadOnly)
	double DurationSec = 1000.0;

	UPROPERTY(BlueprintReadOnly)
	double ScaleFactor = 0.01;

	UPROPERTY(BlueprintReadOnly)
	FString VisualScaleLabel;
};

USTRUCT(BlueprintType)
struct FEncounterData
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly)
	double TcaSeconds = 0.0;

	UPROPERTY(BlueprintReadOnly)
	double MissDistanceMetres = 0.0;

	UPROPERTY(BlueprintReadOnly)
	double RelativeSpeedMps = 0.0;

	UPROPERTY(BlueprintReadOnly)
	FVector RelativePositionUe = FVector::ZeroVector;

	UPROPERTY(BlueprintReadOnly)
	double CollisionProbability = 0.0;

	UPROPERTY(BlueprintReadOnly)
	double CollisionLog10Pc = 0.0;

	UPROPERTY(BlueprintReadOnly)
	FString PcStatus;

	UPROPERTY(BlueprintReadOnly)
	FString RiskClassification;
};

USTRUCT(BlueprintType)
struct FManoeuvreData
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly)
	FString ManoeuvreId;

	UPROPERTY(BlueprintReadOnly)
	double BurnEpochSeconds = 0.0;

	UPROPERTY(BlueprintReadOnly)
	double DeltaVMagnitudeMps = 0.0;

	UPROPERTY(BlueprintReadOnly)
	FString DirectionLabelRtn;

	UPROPERTY(BlueprintReadOnly)
	FVector DeltaVRtn = FVector::ZeroVector;

	UPROPERTY(BlueprintReadOnly)
	FVector DeltaVEci = FVector::ZeroVector;

	UPROPERTY(BlueprintReadOnly)
	FVector DeltaVUe = FVector::ZeroVector;

	UPROPERTY(BlueprintReadOnly)
	FVector SatellitePositionAtBurnUe = FVector::ZeroVector;
};

USTRUCT(BlueprintType)
struct FDemonstrationStep
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly)
	int32 StepIndex = 0;

	UPROPERTY(BlueprintReadOnly)
	FString Identifier;

	UPROPERTY(BlueprintReadOnly)
	double SimulationTimeSec = 0.0;

	UPROPERTY(BlueprintReadOnly)
	FString Headline;

	UPROPERTY(BlueprintReadOnly)
	FString Description;
};

/**
 * Loads and provides access to Python D2 simulation results in Unreal Engine 5.
 */
UCLASS(BlueprintType)
class SATELLITEAVOIDANCE_API USimulationDataBridge : public UObject
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintReadOnly, Category = "Simulation Data")
	bool bIsDataLoaded = false;

	UPROPERTY(BlueprintReadOnly, Category = "Simulation Data")
	FScenarioMetadata Metadata;

	UPROPERTY(BlueprintReadOnly, Category = "Simulation Data")
	FEncounterData NominalEncounter;

	UPROPERTY(BlueprintReadOnly, Category = "Simulation Data")
	FEncounterData PostManoeuvreEncounter;

	UPROPERTY(BlueprintReadOnly, Category = "Simulation Data")
	FManoeuvreData SelectedManoeuvre;

	UPROPERTY(BlueprintReadOnly, Category = "Simulation Data")
	TArray<double> Timestamps;

	UPROPERTY(BlueprintReadOnly, Category = "Simulation Data")
	TArray<FVector> SatNominalPositions;

	UPROPERTY(BlueprintReadOnly, Category = "Simulation Data")
	TArray<FVector> DebrisPositions;

	UPROPERTY(BlueprintReadOnly, Category = "Simulation Data")
	TArray<FVector> SatModifiedPositions;

	UPROPERTY(BlueprintReadOnly, Category = "Simulation Data")
	TArray<FDemonstrationStep> DemonstrationSequence;

	/** Load JSON payload from disk file path. */
	UFUNCTION(BlueprintCallable, Category = "Simulation Data")
	bool LoadSimulationPayloadFromFile(const FString& FilePath);

	/** Interpolate satellite position at current scenario time. */
	UFUNCTION(BlueprintPure, Category = "Simulation Data")
	FVector GetSatellitePositionAtTime(double TimeSeconds, bool bUseModifiedTrajectory) const;

	/** Interpolate debris position at current scenario time. */
	UFUNCTION(BlueprintPure, Category = "Simulation Data")
	FVector GetDebrisPositionAtTime(double TimeSeconds) const;
};

