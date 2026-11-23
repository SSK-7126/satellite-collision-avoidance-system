// AvoidanceInfoPanelWidget.h - Real-Time Mission Control Dashboard & Telemetry HUD in UE5
#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "SatelliteAvoidance/DataBridge/SimulationDataBridge.h"
#include "AvoidanceInfoPanelWidget.generated.h"

class AOrbitSimulationManager;
class AFreeCameraController;

UCLASS()
class SATELLITEAVOIDANCE_API UAvoidanceInfoPanelWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UAvoidanceInfoPanelWidget(const FObjectInitializer& ObjectInitializer);

	UPROPERTY(BlueprintReadWrite, Category = "Simulation")
	AOrbitSimulationManager* SimulationManager = nullptr;

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

	/** Set active camera display name and mode. */
	UFUNCTION(BlueprintCallable, Category = "Camera")
	void UpdateCameraDisplay(const FString& InCamName, bool bInFreeCam);

	/** Update KAN ML telemetry and comparison status. */
	UFUNCTION(BlueprintCallable, Category = "Telemetry")
	void UpdateKanTelemetry(
		const FString& InPredictedRisk,
		const FString& InEstimatedPc,
		const FString& InModelVersion,
		const FString& InStatus,
		const FString& InLatency,
		const FString& InLogDelta,
		const FString& InConcordance,
		const FLinearColor& InStatusCol,
		const FLinearColor& InConcordanceCol
	);

	// Telemetry strings matching approved layout
	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString EncounterPairStr = TEXT("SAT_PAYLOAD_01 vs DEBRIS_PIECE_99");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString SimTimeStr = TEXT("T + 000.00 s");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString RelVelocityStr = TEXT("14.171 m/s");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString NominalTcaStr = TEXT("769.63 s");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString NominalMissDistStr = TEXT("1,563.48 m");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString NominalPcStr = TEXT("3.9575 × 10^-14");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString NominalPcStatusStr = TEXT("NUMERICAL_OK");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString PlannedDeltaVStr = TEXT("3.00 m/s");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString PlannedDirectionStr = TEXT("-R (Radial Inward)");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString PlannedEpochStr = TEXT("169.63 s");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString PlannedStatusStr = TEXT("SIMULATED BURN APPLIED");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString PostTcaStr = TEXT("903.03 s (Shift: +133.40 s)");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString PostMissDistStr = TEXT("2,454.42 m (+890.94 m)");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString PostPcStr = TEXT("1.2387 × 10^-22");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString PostPcStatusStr = TEXT("NUMERICAL_UNDERFLOW");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString OperationalStatusStr = TEXT("PREDICTED SAFE");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString OperationalDetailStr = TEXT("Miss distance exceeds operational threshold (2,000 m)");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString CurrentMilestoneHeadline = TEXT("Initial Orbital Configuration");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString DisplayPlaybackStatus = TEXT("PLAYING (10.0x)");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	FString ActiveCameraName = TEXT("Free Camera");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	bool bFreeCameraActive = true;

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	bool bIsPlayingDisplay = true;

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	double TimeDilationDisplay = 10.0;

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	int32 CurrentStepIndex = 1;

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data")
	int32 TotalStepsCount = 8;

	/** Explicit state flag indicating that post-encounter trajectory has been propagated and evaluated at TCA */
	UPROPERTY(BlueprintReadWrite, Category = "Telemetry Data")
	bool bPostEncounterStateEvaluated = false;

	/** Configurable clearance threshold in metres (default 2000.0 m) */
	UPROPERTY(BlueprintReadWrite, Category = "Telemetry Data")
	double ClearanceThresholdMetres = 2000.0;

	// KAN ML Telemetry & Dual-Model Comparison
	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data - KAN")
	FString KanPredictedRiskStr = TEXT("N/A");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data - KAN")
	FString KanEstimatedPcStr = TEXT("N/A");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data - KAN")
	FString KanModelVersionStr = TEXT("pykan_esa_kelvins_v1.0");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data - KAN")
	FString KanStatusStr = TEXT("BACKEND UNAVAILABLE");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data - KAN")
	FString KanLatencyStr = TEXT("-- ms");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data - KAN")
	FString KanLogDeltaStr = TEXT("N/A");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data - KAN")
	FString DualModelConcordanceStr = TEXT("PHYSICS ONLY (FALLBACK)");

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data - KAN")
	FLinearColor KanStatusColor = FLinearColor(0.95f, 0.6f, 0.1f, 1.0f);

	UPROPERTY(BlueprintReadOnly, Category = "Telemetry Data - KAN")
	FLinearColor ConcordanceColor = FLinearColor(0.2f, 0.8f, 0.4f, 1.0f);

	// Slate Rendering
	virtual int32 NativePaint(
		const FPaintArgs& Args,
		const FGeometry& AllottedGeometry,
		const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements,
		int32 LayerId,
		const FWidgetStyle& InWidgetStyle,
		bool bParentEnabled
	) const override;

	// Interactive Slate Input Events
	virtual FReply NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;
	virtual FReply NativeOnMouseButtonUp(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;
	virtual FReply NativeOnMouseMove(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;
	virtual FReply NativeOnMouseWheel(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;
	virtual FCursorReply NativeOnCursorQuery(const FGeometry& InGeometry, const FPointerEvent& InCursorEvent) override;

private:
	// Dynamic button hitbox identification for mouse clicks
	enum EButtonId
	{
		Btn_None = 0,
		Btn_PlayPause,
		Btn_Reset,
		Btn_StepBack,
		Btn_StepFwd,
		Btn_Speed,
		Btn_Camera,
		Btn_FreeCamToggle,
		Btn_TimelineStep1,
		Btn_TimelineStep2,
		Btn_TimelineStep3,
		Btn_TimelineStep4,
		Btn_TimelineStep5,
		Btn_TimelineStep6,
		Btn_TimelineStep7,
		Btn_TimelineStep8
	};

	struct FPanelRect
	{
		float Left = 0.0f;
		float Top = 0.0f;
		float Right = 0.0f;
		float Bottom = 0.0f;

		FPanelRect() = default;
		FPanelRect(float InL, float InT, float InR, float InB)
			: Left(InL), Top(InT), Right(InR), Bottom(InB) {}

		bool Contains(const FVector2D& Point) const
		{
			return Point.X >= Left && Point.X <= Right && Point.Y >= Top && Point.Y <= Bottom;
		}
	};

	mutable TMap<int32, FPanelRect> ButtonHitBoxes;
	mutable FPanelRect ViewportInteractionRect;
	mutable int32 HoveredButtonId = Btn_None;

	bool bIsOrbiting = false;
	bool bIsPanning = false;
	FVector2D LastMousePosition = FVector2D::ZeroVector;
};
