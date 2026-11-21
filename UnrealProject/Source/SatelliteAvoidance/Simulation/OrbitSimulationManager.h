// OrbitSimulationManager.h - Orchestrates scenario clock, playback, controls, and 8-step sequence
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SatelliteAvoidance/DataBridge/SimulationDataBridge.h"
#include "SatelliteAvoidance/Actors/EarthActor.h"
#include "SatelliteAvoidance/Actors/SatelliteActor.h"
#include "SatelliteAvoidance/Actors/DebrisActor.h"
#include "SatelliteAvoidance/Visualization/OrbitPathActor.h"
#include "SatelliteAvoidance/Visualization/ConjunctionVisualizer.h"
#include "SatelliteAvoidance/Visualization/ManoeuvreVisualizer.h"
#include "SatelliteAvoidance/UI/AvoidanceInfoPanelWidget.h"
#include "OrbitSimulationManager.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnSimulationTimeUpdated, double, CurrentTimeSeconds);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnDemonstrationStepTriggered, const FDemonstrationStep&, CurrentStep);

UCLASS()
class SATELLITEAVOIDANCE_API AOrbitSimulationManager : public AActor
{
	GENERATED_BODY()

public:
	AOrbitSimulationManager();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Data Bridge")
	USimulationDataBridge* DataBridge;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "UI")
	UAvoidanceInfoPanelWidget* AvoidanceWidget;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
	AActor* OverviewCamera;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
	TArray<AActor*> CameraViews;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
	int32 CurrentCameraIndex = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Simulation Clock")
	double CurrentSimulationTime = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Simulation Clock")
	double TimeDilation = 5.0; // 5x real-time playback by default

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Simulation Clock")
	bool bIsPlaying = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Simulation State")
	bool bManoeuvreExecuted = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Demonstration Sequence")
	int32 CurrentStepIndex = 1;

	UPROPERTY(BlueprintAssignable, Category = "Events")
	FOnSimulationTimeUpdated OnTimeUpdated;

	UPROPERTY(BlueprintAssignable, Category = "Events")
	FOnDemonstrationStepTriggered OnStepTriggered;

	// Scene Actor References
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Actors")
	AEarthActor* EarthActor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Actors")
	ASatelliteActor* SatelliteActor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Actors")
	ADebrisActor* DebrisActor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Visualizers")
	AOrbitPathActor* SatNominalPathActor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Visualizers")
	AOrbitPathActor* DebrisPathActor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Visualizers")
	AOrbitPathActor* SatModifiedPathActor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Visualizers")
	AConjunctionVisualizer* ConjunctionVisualizer;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Visualizers")
	AManoeuvreVisualizer* ManoeuvreVisualizer;

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaTime) override;

	/** Load simulation payload and initialize paths and actors. */
	UFUNCTION(BlueprintCallable, Category = "Simulation Control")
	bool InitializeSimulationFromPayload(const FString& PayloadFilePath);

	/** Jump immediately to one of the 8 demonstration sequence steps. */
	UFUNCTION(BlueprintCallable, Category = "Demonstration Sequence")
	void JumpToStep(int32 StepIndex);

	/** Step forward to the next demonstration milestone. */
	UFUNCTION(BlueprintCallable, Category = "Demonstration Sequence")
	void StepForward();

	/** Step backward to the previous demonstration milestone. */
	UFUNCTION(BlueprintCallable, Category = "Demonstration Sequence")
	void StepBackward();

	/** Play / Pause toggle. */
	UFUNCTION(BlueprintCallable, Category = "Simulation Control")
	void TogglePlayPause();

	/** Reset simulation to initial epoch (t = 0.0s). */
	UFUNCTION(BlueprintCallable, Category = "Simulation Control")
	void ResetSimulation();

	/** Increase simulation playback speed (Time Dilation). */
	UFUNCTION(BlueprintCallable, Category = "Simulation Control")
	void IncreaseSpeed();

	/** Decrease simulation playback speed (Time Dilation). */
	UFUNCTION(BlueprintCallable, Category = "Simulation Control")
	void DecreaseSpeed();

	/** Set exact simulation playback speed. */
	UFUNCTION(BlueprintCallable, Category = "Simulation Control")
	void SetTimeDilation(double NewDilation);

	/** Cycle between available camera views in the scenario. */
	UFUNCTION(BlueprintCallable, Category = "Camera Control")
	void CycleCameraView();

	/** Switch active camera view to match milestone context. */
	UFUNCTION(BlueprintCallable, Category = "Camera Control")
	void SetCameraForStep(int32 StepIndex);

	// Key binding helper functions for steps 1-8
	void JumpToStep1() { JumpToStep(1); }
	void JumpToStep2() { JumpToStep(2); }
	void JumpToStep3() { JumpToStep(3); }
	void JumpToStep4() { JumpToStep(4); }
	void JumpToStep5() { JumpToStep(5); }
	void JumpToStep6() { JumpToStep(6); }
	void JumpToStep7() { JumpToStep(7); }
	void JumpToStep8() { JumpToStep(8); }

protected:
	void SetupPlayerInput();
};
