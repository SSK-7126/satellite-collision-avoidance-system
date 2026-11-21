// AvoidanceInfoPanelWidget.h - Real-Time HUD Telemetry Information Panel in UE5
#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SatelliteAvoidance/DataBridge/SimulationDataBridge.h"
#include "AvoidanceInfoPanelWidget.generated.h"

UCLASS()
class SATELLITEAVOIDANCE_API UAvoidanceInfoPanelWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UAvoidanceInfoPanelWidget(const FObjectInitializer& ObjectInitializer);

	/** Update telemetry display values from simulation state. */
	UFUNCTION(BlueprintCallable, Category = "Telemetry")
	void UpdateTelemetry(
		double CurrentTimeSeconds,
		const FString& SatId,
		const FString& DebrisId,
		const FEncounterData& Nominal,
		const FEncounterData& PostManoeuvre,
		const FManoeuvreData& Manoeuvre,
		bool bManoeuvreHasExecuted
	);

	/** Update playback state and controls for HUD display. */
	UFUNCTION(BlueprintCallable, Category = "Telemetry")
	void UpdatePlaybackControls(bool bPlaying, double InTimeDilation, int32 StepIndex, int32 TotalSteps);

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString DisplaySimulationTime;

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString DisplayObjects;

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString DisplayTca;

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString DisplayMissDistance;

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString DisplayRelativeSpeed;

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString DisplayDeltaV;

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString DisplayBurnDirection;

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString DisplayCollisionProbability;

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString DisplayPcStatus;

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString DisplayRiskComparison;

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString CurrentMilestoneHeadline = TEXT("Step 1 / 8: Initialize Orbital Simulation");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString DisplayPlaybackStatus = TEXT("PLAYING (5.0x)");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	bool bIsPlayingDisplay = true;

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	double TimeDilationDisplay = 5.0;

	virtual int32 NativePaint(
		const FPaintArgs& Args,
		const FGeometry& AllottedGeometry,
		const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements,
		int32 LayerId,
		const FWidgetStyle& InWidgetStyle,
		bool bParentEnabled
	) const override;
};
