// OrbitSimulationManager.h - Orchestrates scenario clock, playback, controls, free camera, and 8-step sequence
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Interfaces/IHttpRequest.h"
#include "Interfaces/IHttpResponse.h"
#include "SatelliteAvoidance/DataBridge/SimulationDataBridge.h"
#include "SatelliteAvoidance/Actors/EarthActor.h"
#include "SatelliteAvoidance/Actors/SatelliteActor.h"
#include "SatelliteAvoidance/Actors/DebrisActor.h"
#include "SatelliteAvoidance/Visualization/OrbitPathActor.h"
#include "SatelliteAvoidance/Visualization/ConjunctionVisualizer.h"
#include "SatelliteAvoidance/Visualization/ManoeuvreVisualizer.h"
#include "SatelliteAvoidance/Camera/FreeCameraController.h"
#include "OrbitSimulationManager.generated.h"

class UAvoidanceInfoPanelWidget;

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

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
	AFreeCameraController* FreeCameraController;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
	bool bUseFreeCamera = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
	AActor* OverviewCamera;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
	TArray<AActor*> CameraViews;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
	int32 CurrentCameraIndex = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Simulation Clock")
	double CurrentSimulationTime = 0.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Simulation Clock")
	double TimeDilation = 10.0; // 10x real-time playback by default matching reference

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

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Automation")
	bool bAutoCaptureReview = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Automation")
	int32 AutoCaptureFrame = 0;

	FTimerHandle ReviewTimerHandle;
	int32 ReviewCaptureTickCount = 0;
	void OnReviewCaptureTick();

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

	/** Cycle simulation playback speed between tiers (1x -> 2x -> 5x -> 10x -> 25x -> 50x -> 100x -> 200x). */
	UFUNCTION(BlueprintCallable, Category = "Simulation Control")
	void CycleSpeed();

	/** Increase simulation playback speed (Time Dilation). */
	UFUNCTION(BlueprintCallable, Category = "Simulation Control")
	void IncreaseSpeed();

	/** Decrease simulation playback speed (Time Dilation). */
	UFUNCTION(BlueprintCallable, Category = "Simulation Control")
	void DecreaseSpeed();

	/** Set exact simulation playback speed. */
	UFUNCTION(BlueprintCallable, Category = "Simulation Control")
	void SetTimeDilation(double NewDilation);

	/** Toggle Free Camera mode ON / OFF. */
	UFUNCTION(BlueprintCallable, Category = "Camera Control")
	void ToggleFreeCamera();

	/** Cycle between available preset camera views in the scenario. */
	UFUNCTION(BlueprintCallable, Category = "Camera Control")
	void CycleCameraView();

	/** Switch active camera view to match milestone context. */
	UFUNCTION(BlueprintCallable, Category = "Camera Control")
	void SetCameraForStep(int32 StepIndex);

	/** Select and frame an actor in the 3D scene (Earth, Satellite, Debris). */
	UFUNCTION(BlueprintCallable, Category = "Camera Control")
	void SelectActor(AActor* InActor);

	/** Frame the currently selected actor with the camera. */
	UFUNCTION(BlueprintCallable, Category = "Camera Control")
	void FrameSelectedActor();

	/** Reset camera to the default Mission Control overview framing. */
	UFUNCTION(BlueprintCallable, Category = "Camera Control")
	void ResetCameraToOverview();

	/** Get current active camera display name. */
	UFUNCTION(BlueprintCallable, Category = "Camera Control")
	FString GetCurrentCameraName() const;

	/** Check if free camera mode is currently active. */
	UFUNCTION(BlueprintCallable, Category = "Camera Control")
	bool IsFreeCameraActive() const { return bUseFreeCamera; }

	AFreeCameraController* GetFreeCameraController() const { return FreeCameraController; }

	// Key binding helper functions for steps 1-8
	void JumpToStep1() { JumpToStep(1); }
	void JumpToStep2() { JumpToStep(2); }
	void JumpToStep3() { JumpToStep(3); }
	void JumpToStep4() { JumpToStep(4); }
	void JumpToStep5() { JumpToStep(5); }
	void JumpToStep6() { JumpToStep(6); }
	void JumpToStep7() { JumpToStep(7); }
	void JumpToStep8() { JumpToStep(8); }

	/** Request KAN ML prediction asynchronously from the backend REST API. */
	UFUNCTION(BlueprintCallable, Category = "KAN Prediction")
	void RequestKanPrediction(int32 StepIndex);

	/** Callback for asynchronous KAN HTTP response. */
	void OnKanResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bConnectedSuccessfully);

	/** Set KAN service URL (defaults to http://127.0.0.1:8000). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "KAN Prediction")
	FString KanServiceBaseUrl = TEXT("http://127.0.0.1:8000");

	int32 LastKanRequestedStep = -1;
	bool bKanRequestInFlight = false;
	double LastKanRequestTime = -100.0;

protected:
	void SetupPlayerInput();
};
