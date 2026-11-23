// AvoidanceInfoPanelWidget.cpp - Real-Time Mission Control Dashboard & Telemetry HUD in UE5
#include "AvoidanceInfoPanelWidget.h"
#include "SatelliteAvoidance/Simulation/OrbitSimulationManager.h"
#include "SatelliteAvoidance/Camera/FreeCameraController.h"
#include "Rendering/DrawElements.h"
#include "Rendering/DrawElementTypes.h"
#include "Styling/CoreStyle.h"
#include "Styling/AppStyle.h"
#include "Framework/Application/SlateApplication.h"
#include "Kismet/GameplayStatics.h"
#include "GameFramework/PlayerController.h"

UAvoidanceInfoPanelWidget::UAvoidanceInfoPanelWidget(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	bIsPlayingDisplay = true;
	TimeDilationDisplay = 10.0;
	CurrentStepIndex = 1;
	TotalStepsCount = 8;
	DisplayPlaybackStatus = TEXT("PLAYING (10.0x)");
	ActiveCameraName = TEXT("Free Camera");
	bFreeCameraActive = true;
}

void UAvoidanceInfoPanelWidget::UpdateTelemetry(
	double CurrentTimeSeconds,
	const FString& SatId,
	const FString& DebrisId,
	const FEncounterData& Nominal,
	const FEncounterData& PostManoeuvre,
	const FManoeuvreData& Manoeuvre,
	bool bManoeuvreHasExecuted
)
{
	EncounterPairStr = FString::Printf(TEXT("%s vs %s"), *SatId, *DebrisId);
	SimTimeStr = FString::Printf(TEXT("T + %06.2f s"), CurrentTimeSeconds);
	RelVelocityStr = FString::Printf(TEXT("%.3f m/s"), Nominal.RelativeSpeedMps);

	NominalTcaStr = FString::Printf(TEXT("%.2f s"), Nominal.TcaSeconds);
	NominalMissDistStr = FString::Printf(TEXT("%.2f m"), Nominal.MissDistanceMetres);
	NominalPcStr = FString::Printf(TEXT("%.4e"), Nominal.CollisionProbability);
	NominalPcStatusStr = Nominal.PcStatus.IsEmpty() ? TEXT("NUMERICAL_OK") : Nominal.PcStatus;

	PlannedDeltaVStr = FString::Printf(TEXT("%.2f m/s"), Manoeuvre.DeltaVMagnitudeMps);
	PlannedDirectionStr = FString::Printf(TEXT("%s (Radial Inward)"), *Manoeuvre.DirectionLabelRtn);
	PlannedEpochStr = FString::Printf(TEXT("%.2f s"), Manoeuvre.BurnEpochSeconds);
	PlannedStatusStr = bManoeuvreHasExecuted ? TEXT("SIMULATED BURN APPLIED") : TEXT("PLANNED MANOEUVRE");

	const double TcaShift = PostManoeuvre.TcaSeconds - Nominal.TcaSeconds;
	const double MissImprovement = PostManoeuvre.MissDistanceMetres - Nominal.MissDistanceMetres;

	PostTcaStr = FString::Printf(TEXT("%.2f s (Shift: +%.2f s)"), PostManoeuvre.TcaSeconds, TcaShift);
	PostMissDistStr = FString::Printf(TEXT("%.2f m (+%.2f m)"), PostManoeuvre.MissDistanceMetres, MissImprovement);
	PostPcStr = FString::Printf(TEXT("%.4e"), PostManoeuvre.CollisionProbability);
	PostPcStatusStr = PostManoeuvre.PcStatus.IsEmpty() ? TEXT("NUMERICAL_UNDERFLOW") : PostManoeuvre.PcStatus;

	// Strict state validation gate for encounter completion:
	// 1. Step navigation alone must NEVER establish encounter completion.
	// 2. The manoeuvre must have been executed in simulation (bManoeuvreHasExecuted).
	// 3. Simulation time must have reached or passed post-manoeuvre TCA (bTcaReached).
	// 4. The post-encounter propagated state must actually have been evaluated (bPostEncounterStateEvaluated).
	// 5. The calculated separation must be valid (finite, positive) and greater than or equal to configured clearance threshold.
	// 6. Invalid, missing, or stale state data must never produce a completed status.
	const bool bValidTca = (PostManoeuvre.TcaSeconds > 0.0 && !FMath::IsNaN(PostManoeuvre.TcaSeconds) && FMath::IsFinite(PostManoeuvre.TcaSeconds));
	const bool bTcaReached = bValidTca && (CurrentTimeSeconds >= PostManoeuvre.TcaSeconds);
	const bool bValidPostData = (PostManoeuvre.MissDistanceMetres > 0.0 && !FMath::IsNaN(PostManoeuvre.MissDistanceMetres) && FMath::IsFinite(PostManoeuvre.MissDistanceMetres));
	const bool bClearanceAchieved = bValidPostData && (PostManoeuvre.MissDistanceMetres >= ClearanceThresholdMetres);

	if (bManoeuvreHasExecuted && bTcaReached && bPostEncounterStateEvaluated && bValidPostData)
	{
		if (bClearanceAchieved)
		{
			OperationalStatusStr = TEXT("SIMULATED ENCOUNTER COMPLETED \u2014 CLEARANCE ACHIEVED");
			OperationalDetailStr = TEXT("Simulated encounter epoch passed; evaluated post-encounter state confirms clearance achieved (> 2,000 m)");
		}
		else
		{
			OperationalStatusStr = TEXT("SIMULATED ENCOUNTER COMPLETED \u2014 CLEARANCE NOT ACHIEVED");
			OperationalDetailStr = TEXT("Simulated encounter passed; evaluated separation is below the operational threshold (2,000 m)");
		}
	}
	else if (bManoeuvreHasExecuted || CurrentStepIndex >= 6)
	{
		OperationalStatusStr = TEXT("PREDICTED SAFE (POST-BURN)");
		OperationalDetailStr = TEXT("Post-burn trajectory predicts miss distance exceeds operational threshold (2,000 m)");
	}
	else if (CurrentTimeSeconds >= 120.0 || CurrentStepIndex >= 3)
	{
		OperationalStatusStr = TEXT("CRITICAL RISK");
		OperationalDetailStr = TEXT("Predicted miss distance below safety threshold (2,000 m)");
	}
	else
	{
		OperationalStatusStr = TEXT("NOMINAL MONITORING");
		OperationalDetailStr = TEXT("Spacecraft operating on verified orbital clearance");
	}
}

void UAvoidanceInfoPanelWidget::UpdatePlaybackControls(bool bPlaying, double InTimeDilation, int32 StepIndex, int32 TotalSteps)
{
	bIsPlayingDisplay = bPlaying;
	TimeDilationDisplay = InTimeDilation;
	CurrentStepIndex = FMath::Clamp(StepIndex, 1, TotalSteps);
	TotalStepsCount = TotalSteps;

	if (bPlaying)
	{
		DisplayPlaybackStatus = FString::Printf(TEXT("PLAYING (%.1fx)"), InTimeDilation);
	}
	else
	{
		DisplayPlaybackStatus = TEXT("PAUSED");
	}

	static const TCHAR* StepTitles[] = {
		TEXT("Initial Orbital Configuration"),
		TEXT("Conjunction Detection"),
		TEXT("Risk Assessment"),
		TEXT("Manoeuvre Planning"),
		TEXT("Pre-Burn Approach"),
		TEXT("Impulsive Burn Execution"),
		TEXT("Post-Burn Trajectory Evolution"),
		TEXT("Final Predicted Encounter Assessment")
	};
	if (CurrentStepIndex >= 1 && CurrentStepIndex <= 8)
	{
		CurrentMilestoneHeadline = StepTitles[CurrentStepIndex - 1];
	}
}

void UAvoidanceInfoPanelWidget::UpdateCameraDisplay(const FString& InCamName, bool bInFreeCam)
{
	ActiveCameraName = InCamName;
	bFreeCameraActive = bInFreeCam;
}

void UAvoidanceInfoPanelWidget::UpdateKanTelemetry(
	const FString& InPredictedRisk,
	const FString& InEstimatedPc,
	const FString& InModelVersion,
	const FString& InStatus,
	const FString& InLatency,
	const FString& InLogDelta,
	const FString& InConcordance,
	const FLinearColor& InStatusCol,
	const FLinearColor& InConcordanceCol
)
{
	KanPredictedRiskStr = InPredictedRisk;
	KanEstimatedPcStr = InEstimatedPc;
	KanModelVersionStr = InModelVersion;
	KanStatusStr = InStatus;
	KanLatencyStr = InLatency;
	KanLogDeltaStr = InLogDelta;
	DualModelConcordanceStr = InConcordance;
	KanStatusColor = InStatusCol;
	ConcordanceColor = InConcordanceCol;
}

int32 UAvoidanceInfoPanelWidget::NativePaint(
	const FPaintArgs& Args,
	const FGeometry& AllottedGeometry,
	const FSlateRect& MyCullingRect,
	FSlateWindowElementList& OutDrawElements,
	int32 LayerId,
	const FWidgetStyle& InWidgetStyle,
	bool bParentEnabled
) const
{
	Super::NativePaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);

	const FVector2D LocalSize = AllottedGeometry.GetLocalSize();
	const float ScreenW = static_cast<float>(LocalSize.X);
	const float ScreenH = static_cast<float>(LocalSize.Y);

	const FSlateBrush* WhiteBrush = FCoreStyle::Get().GetBrush(TEXT("WhiteBrush"));

	ButtonHitBoxes.Empty();

	// Premium Aerospace Color Palette matching deeporbit.space aesthetic
	const FLinearColor ColorNavyBg(0.012f, 0.028f, 0.065f, 0.88f);
	const FLinearColor ColorCardBg(0.016f, 0.040f, 0.095f, 0.84f);
	const FLinearColor ColorCyanBorder(0.0f, 0.78f, 1.0f, 0.75f);
	const FLinearColor ColorCyanGlow(0.0f, 0.95f, 1.0f, 1.0f);
	const FLinearColor ColorGreen(0.0f, 0.95f, 0.45f, 1.0f);
	const FLinearColor ColorAmber(1.0f, 0.65f, 0.1f, 1.0f);
	const FLinearColor ColorRed(1.0f, 0.22f, 0.25f, 1.0f);
	const FLinearColor ColorTextMuted(0.60f, 0.78f, 0.92f, 0.95f);
	const FLinearColor ColorHover(0.0f, 0.5f, 0.85f, 0.35f);

	// Crisp typography
	const FSlateFontInfo FontTitle = FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 11);
	const FSlateFontInfo FontSubtitle = FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), 8);
	const FSlateFontInfo FontHeader = FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 9);
	const FSlateFontInfo FontSmall = FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), 8);
	const FSlateFontInfo FontStatus = FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 11);
	const FSlateFontInfo FontButton = FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 8);

	auto DrawBox = [&](float X, float Y, float W, float H, const FLinearColor& Fill, const FLinearColor& Border, float BorderThick = 1.0f, int32 InLayer = 0)
	{
		const int32 UseLayer = (InLayer > 0) ? InLayer : LayerId;
		FPaintGeometry Geom = AllottedGeometry.ToPaintGeometry(FVector2f(W, H), FSlateLayoutTransform(FVector2f(X, Y)));
		FSlateDrawElement::MakeBox(OutDrawElements, UseLayer, Geom, WhiteBrush, ESlateDrawEffect::None, Fill);
		if (BorderThick > 0.0f && Border.A > 0.0f)
		{
			FSlateDrawElement::MakeGeometryOutline(OutDrawElements, UseLayer + 1, Geom, Border, ESlateDrawEffect::None, true, BorderThick);
		}
	};

	auto DrawButton = [&](int32 BtnId, float X, float Y, float W, float H, const FString& Label, const FLinearColor& BorderCol, const FLinearColor& TextCol, bool bActive = false)
	{
		ButtonHitBoxes.Add(BtnId, FPanelRect(X, Y, X + W, Y + H));
		const bool bHovered = (HoveredButtonId == BtnId);
		FLinearColor Fill = bActive ? FLinearColor(0.04f, 0.25f, 0.12f, 0.95f) : (bHovered ? ColorHover : FLinearColor(0.02f, 0.07f, 0.16f, 0.90f));
		FLinearColor Border = bHovered ? ColorCyanGlow : BorderCol;
		DrawBox(X, Y, W, H, Fill, Border, bActive ? 1.8f : 1.0f, LayerId + 2);

		FPaintGeometry TextGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(X + 6.0f, Y + (H * 0.5f) - 6.0f)));
		FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, TextGeom, Label, FontButton, ESlateDrawEffect::None, TextCol);
	};

	// =========================================================================
	// 1. TOP AEROSPACE COMMAND RIBBON (Integrated Identity + Controls)
	// =========================================================================
	const float HeaderX = 8.0f;
	const float HeaderY = 8.0f;
	const float HeaderW = ScreenW - 16.0f;
	const float HeaderH = 46.0f;

	DrawBox(HeaderX, HeaderY, HeaderW, HeaderH, ColorNavyBg, ColorCyanBorder, 1.2f);
	DrawBox(HeaderX + 1.0f, HeaderY + HeaderH - 2.0f, HeaderW - 2.0f, 2.0f, ColorCyanGlow, FLinearColor::Transparent, 0.0f);

	// ICPS Identity
	FPaintGeometry TitleGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(HeaderX + 12.0f, HeaderY + 6.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 2, TitleGeom, TEXT("ICPS \u2013 SATELLITE COLLISION AVOIDANCE SYSTEM"), FontTitle, ESlateDrawEffect::None, FLinearColor::White);

	FPaintGeometry SubtitleGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(HeaderX + 12.0f, HeaderY + 24.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 2, SubtitleGeom, TEXT("AUTONOMOUS CONJUNCTION ASSESSMENT & DUAL-MODEL VERIFICATION"), FontSubtitle, ESlateDrawEffect::None, ColorTextMuted);

	// Playback Controls integrated directly into top bar
	float CtrlBtnX = HeaderX + 410.0f;
	const float CtrlBtnY = HeaderY + 8.0f;
	const float CtrlBtnH = 28.0f;

	// Button: Play / Pause
	const FString PlayLabel = bIsPlayingDisplay ? TEXT("|| Pause") : TEXT("\u25B6 Play");
	DrawButton(Btn_PlayPause, CtrlBtnX, CtrlBtnY, 68.0f, CtrlBtnH, PlayLabel, ColorCyanBorder, FLinearColor::White);
	CtrlBtnX += 74.0f;

	// Button: Reset
	DrawButton(Btn_Reset, CtrlBtnX, CtrlBtnY, 64.0f, CtrlBtnH, TEXT("\u21BB Reset"), ColorCyanBorder, FLinearColor::White);
	CtrlBtnX += 70.0f;

	// Button: Step Backward
	DrawButton(Btn_StepBack, CtrlBtnX, CtrlBtnY, 74.0f, CtrlBtnH, TEXT("\u25C0 Step \u2212"), ColorCyanBorder, FLinearColor::White);
	CtrlBtnX += 80.0f;

	// Button: Step Forward
	DrawButton(Btn_StepFwd, CtrlBtnX, CtrlBtnY, 74.0f, CtrlBtnH, TEXT("\u25B6 Step +"), ColorCyanBorder, FLinearColor::White);
	CtrlBtnX += 84.0f;

	// Speed Selector
	const FString SpeedText = FString::Printf(TEXT("Speed: %.1fx \u2304"), TimeDilationDisplay);
	DrawButton(Btn_Speed, CtrlBtnX, CtrlBtnY, 96.0f, CtrlBtnH, SpeedText, ColorCyanBorder, ColorCyanGlow);
	CtrlBtnX += 104.0f;

	// Camera Selector Button
	const FString CamText = FString::Printf(TEXT("Camera: %s \u2304"), *ActiveCameraName);
	DrawButton(Btn_Camera, CtrlBtnX, CtrlBtnY, 150.0f, CtrlBtnH, CamText, ColorCyanBorder, FLinearColor::White);
	CtrlBtnX += 158.0f;

	// Free Camera Toggle Button
	const FString FreeCamText = bFreeCameraActive ? TEXT("\u25CE Free Cam: ON") : TEXT("\u25CE Free Cam: OFF");
	DrawButton(Btn_FreeCamToggle, CtrlBtnX, CtrlBtnY, 125.0f, CtrlBtnH, FreeCamText, bFreeCameraActive ? ColorGreen : ColorAmber, bFreeCameraActive ? ColorGreen : ColorAmber, bFreeCameraActive);

	// Status Badge Pill
	const float BadgeW = 110.0f;
	const float BadgeH = 26.0f;
	const float BadgeX = HeaderX + HeaderW - BadgeW - 10.0f;
	const float BadgeY = HeaderY + 9.0f;
	const FLinearColor BadgeFill = bIsPlayingDisplay ? FLinearColor(0.04f, 0.28f, 0.12f, 0.95f) : FLinearColor(0.28f, 0.16f, 0.02f, 0.95f);
	const FLinearColor BadgeBorder = bIsPlayingDisplay ? ColorGreen : ColorAmber;
	const FLinearColor BadgeTextCol = bIsPlayingDisplay ? FLinearColor(0.3f, 1.0f, 0.5f, 1.0f) : FLinearColor(1.0f, 0.8f, 0.2f, 1.0f);
	DrawBox(BadgeX, BadgeY, BadgeW, BadgeH, BadgeFill, BadgeBorder, 1.2f, LayerId + 2);

	FPaintGeometry BadgeTextGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(BadgeX + 10.0f, BadgeY + 5.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, BadgeTextGeom, DisplayPlaybackStatus, FontButton, ESlateDrawEffect::None, BadgeTextCol);

	// =========================================================================
	// 2. LEFT AEROSPACE SURVEILLANCE COLUMN (Real Mission Asset Registry)
	// =========================================================================
	const float LeftX = 14.0f;
	const float LeftW = 280.0f;

	// -------------------------------------------------------------------------
	// Card 2A: "PRIMARY PROTECTED ASSET" (Top-Left)
	// -------------------------------------------------------------------------
	const float SatCardY = 58.0f;
	const float SatCardH = 175.0f;
	DrawBox(LeftX, SatCardY, LeftW, SatCardH, ColorNavyBg, ColorCyanBorder, 1.0f);

	// Header Bar
	DrawBox(LeftX, SatCardY, LeftW, 20.0f, FLinearColor(0.02f, 0.07f, 0.16f, 0.95f), FLinearColor::Transparent, 0.0f, LayerId + 2);
	FPaintGeometry SatHeadGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(LeftX + 8.0f, SatCardY + 3.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, SatHeadGeom, TEXT("\u25C6 PRIMARY PROTECTED ASSET"), FontButton, ESlateDrawEffect::None, ColorCyanGlow);

	float SatRowY = SatCardY + 26.0f;
	auto DrawSatDataRow = [&](const FString& Label, const FString& Value, const FLinearColor& ValCol = FLinearColor::White)
	{
		FPaintGeometry LGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(LeftX + 10.0f, SatRowY)));
		FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, LGeom, Label, FontSmall, ESlateDrawEffect::None, ColorTextMuted);

		FPaintGeometry VGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(LeftX + 125.0f, SatRowY)));
		FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, VGeom, Value, FontSmall, ESlateDrawEffect::None, ValCol);
		SatRowY += 16.0f;
	};

	DrawSatDataRow(TEXT("Spacecraft:"), TEXT("CARTOSAT-3 (LEO)"), ColorCyanGlow);
	DrawSatDataRow(TEXT("Payload ID:"), TEXT("SAT_PAYLOAD_01"));
	DrawSatDataRow(TEXT("Orbit Regime:"), TEXT("Sun-Synchronous (SSO)"));
	DrawSatDataRow(TEXT("Mean Altitude:"), TEXT("622.0 km"));
	DrawSatDataRow(TEXT("Orbital Inclination:"), TEXT("97.87\u00B0"));
	DrawSatDataRow(TEXT("Orbital Velocity:"), TEXT("7.55 km/s"));
	DrawSatDataRow(TEXT("Propagator:"), TEXT("RK4 Ephemeris (D1/D2)"), ColorGreen);
	DrawSatDataRow(TEXT("Operational Mode:"), (CurrentStepIndex >= 6) ? TEXT("AUTONOMOUS RETARGET") : TEXT("NOMINAL ORBIT"), (CurrentStepIndex >= 6) ? ColorGreen : ColorCyanGlow);

	// -------------------------------------------------------------------------
	// Card 2B: "SECONDARY ENCOUNTER OBJECT" (Mid-Left)
	// -------------------------------------------------------------------------
	const float DebCardY = SatCardY + SatCardH + 8.0f;
	const float DebCardH = 160.0f;
	DrawBox(LeftX, DebCardY, LeftW, DebCardH, ColorNavyBg, ColorCyanBorder, 1.0f);

	// Header Bar
	DrawBox(LeftX, DebCardY, LeftW, 20.0f, FLinearColor(0.02f, 0.07f, 0.16f, 0.95f), FLinearColor::Transparent, 0.0f, LayerId + 2);
	FPaintGeometry DebHeadGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(LeftX + 8.0f, DebCardY + 3.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, DebHeadGeom, TEXT("\u25B2 SECONDARY ENCOUNTER OBJECT"), FontButton, ESlateDrawEffect::None, ColorAmber);

	float DebRowY = DebCardY + 26.0f;
	auto DrawDebDataRow = [&](const FString& Label, const FString& Value, const FLinearColor& ValCol = FLinearColor::White)
	{
		FPaintGeometry LGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(LeftX + 10.0f, DebRowY)));
		FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, LGeom, Label, FontSmall, ESlateDrawEffect::None, ColorTextMuted);

		FPaintGeometry VGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(LeftX + 125.0f, DebRowY)));
		FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, VGeom, Value, FontSmall, ESlateDrawEffect::None, ValCol);
		DebRowY += 16.0f;
	};

	DrawDebDataRow(TEXT("Threat Object:"), TEXT("SL-16 R/B Fragment"), ColorAmber);
	DrawDebDataRow(TEXT("Catalog ID:"), TEXT("DEBRIS_PIECE_99"));
	DrawDebDataRow(TEXT("Classification:"), TEXT("Tracked Rocket Debris"));
	DrawDebDataRow(TEXT("Relative Speed:"), RelVelocityStr, ColorAmber);
	DrawDebDataRow(TEXT("Crossing Angle:"), TEXT("5.76\u00B0 (Descending Node)"));
	DrawDebDataRow(TEXT("Radar Cross Sec:"), TEXT("0.85 m\u00B2"));
	DrawDebDataRow(TEXT("Encounter Status:"), (CurrentStepIndex >= 6) ? TEXT("CLEARED (SAFE PASS)") : TEXT("COLLISION HAZARD"), (CurrentStepIndex >= 6) ? ColorGreen : ColorRed);

	// -------------------------------------------------------------------------
	// Card 2C: "ORBITAL REFERENCE GRID & HAZARD BADGE" (Bottom-Left)
	// -------------------------------------------------------------------------
	const float ShellCardY = DebCardY + DebCardH + 8.0f;
	const float ShellCardH = 155.0f;
	DrawBox(LeftX, ShellCardY, LeftW, ShellCardH, ColorNavyBg, ColorCyanBorder, 1.0f);

	// Header Bar
	DrawBox(LeftX, ShellCardY, LeftW, 20.0f, FLinearColor(0.02f, 0.07f, 0.16f, 0.95f), FLinearColor::Transparent, 0.0f, LayerId + 2);
	FPaintGeometry ShellHeadGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(LeftX + 8.0f, ShellCardY + 3.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, ShellHeadGeom, TEXT("\u25CE ORBITAL REFERENCE GRID"), FontButton, ESlateDrawEffect::None, ColorCyanGlow);

	float ShellRowY = ShellCardY + 26.0f;
	auto DrawShellDataRow = [&](const FString& Label, const FString& Value, const FLinearColor& ValCol = FLinearColor::White)
	{
		FPaintGeometry LGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(LeftX + 10.0f, ShellRowY)));
		FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, LGeom, Label, FontSmall, ESlateDrawEffect::None, ColorTextMuted);

		FPaintGeometry VGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(LeftX + 125.0f, ShellRowY)));
		FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, VGeom, Value, FontSmall, ESlateDrawEffect::None, ValCol);
		ShellRowY += 16.0f;
	};

	DrawShellDataRow(TEXT("Grid Shells:"), TEXT("LEO Reference Envelopes"));
	DrawShellDataRow(TEXT("Classification:"), TEXT("[Illustrative Guide Shells]"), ColorTextMuted);
	DrawShellDataRow(TEXT("Trajectory Count:"), TEXT("3 Propagated + 9 Reference"));

	// Dynamic Risk Status Callout Pill inside Card 2C
	ShellRowY += 4.0f;
	const FString DynamicRiskText = (CurrentStepIndex >= 6) ? TEXT("RESOLVED: SAFE CLEARANCE") : ((CurrentStepIndex >= 3) ? TEXT("ALERT: CRITICAL CONJUNCTION") : TEXT("MONITORING: NOMINAL ORBIT"));
	const FLinearColor DynamicRiskCol = (CurrentStepIndex >= 6) ? ColorGreen : ((CurrentStepIndex >= 3) ? ColorRed : ColorAmber);
	const FLinearColor DynamicRiskFill = (CurrentStepIndex >= 6) ? FLinearColor(0.02f, 0.18f, 0.08f, 0.90f) : ((CurrentStepIndex >= 3) ? FLinearColor(0.24f, 0.04f, 0.06f, 0.90f) : FLinearColor(0.18f, 0.10f, 0.02f, 0.90f));

	DrawBox(LeftX + 8.0f, ShellRowY, LeftW - 16.0f, 26.0f, DynamicRiskFill, DynamicRiskCol, 1.2f, LayerId + 2);
	FPaintGeometry DynRiskGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(LeftX + 14.0f, ShellRowY + 5.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, DynRiskGeom, DynamicRiskText, FontButton, ESlateDrawEffect::None, DynamicRiskCol);

	// =========================================================================
	// 3. RIGHT AEROSPACE TELEMETRY COLUMN (Scientific Telemetry & KAN Gate)
	// =========================================================================
	const float RightW = 345.0f;
	const float RightX = ScreenW - RightW - 14.0f;

	// -------------------------------------------------------------------------
	// Card 3A: "MISSION TELEMETRY (D1/D2 PHYSICS)" (Top-Right)
	// -------------------------------------------------------------------------
	const float RightTelY = 58.0f;
	const float RightTelH = 205.0f;
	DrawBox(RightX, RightTelY, RightW, RightTelH, ColorNavyBg, ColorCyanBorder, 1.0f);

	DrawBox(RightX, RightTelY, RightW, 20.0f, FLinearColor(0.02f, 0.07f, 0.16f, 0.95f), FLinearColor::Transparent, 0.0f, LayerId + 2);
	FPaintGeometry TelHeadGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(RightX + 8.0f, RightTelY + 3.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, TelHeadGeom, TEXT("\u25C6 CONJUNCTION TELEMETRY (D1/D2 ASTRODYNAMICS)"), FontButton, ESlateDrawEffect::None, ColorCyanGlow);

	float TelRowY = RightTelY + 26.0f;
	auto DrawTelDataRow = [&](const FString& Label, const FString& Value, const FLinearColor& ValCol = FLinearColor::White)
	{
		FPaintGeometry LGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(RightX + 10.0f, TelRowY)));
		FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, LGeom, Label, FontSmall, ESlateDrawEffect::None, ColorTextMuted);

		FPaintGeometry VGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(RightX + 145.0f, TelRowY)));
		FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, VGeom, Value, FontSmall, ESlateDrawEffect::None, ValCol);
		TelRowY += 16.0f;
	};

	DrawTelDataRow(TEXT("Encounter Pair:"), EncounterPairStr);
	DrawTelDataRow(TEXT("Simulation Epoch:"), SimTimeStr);
	DrawTelDataRow(TEXT("Relative Velocity:"), RelVelocityStr);
	DrawTelDataRow(TEXT("Nominal Miss Distance:"), NominalMissDistStr, ColorAmber);
	DrawTelDataRow(TEXT("Collision Prob (Pc):"), NominalPcStr, (NominalPcStr.Contains(TEXT("1.0000")) ? ColorRed : ColorAmber));
	DrawTelDataRow(TEXT("Planned \u0394v:"), PlannedDeltaVStr, ColorGreen);
	DrawTelDataRow(TEXT("Burn Execution Epoch:"), PlannedEpochStr);
	DrawTelDataRow(TEXT("Post-Manoeuvre Miss:"), PostMissDistStr, ColorGreen);
	DrawTelDataRow(TEXT("Residual Collision Prob:"), PostPcStr, ColorGreen);
	DrawTelDataRow(TEXT("Manoeuvre Status:"), PlannedStatusStr, (CurrentStepIndex >= 6) ? ColorGreen : ColorAmber);

	// -------------------------------------------------------------------------
	// Card 3B: "ESA KAN NEURAL NETWORK GATE" (Mid-Right)
	// -------------------------------------------------------------------------
	const float MidRightY = RightTelY + RightTelH + 8.0f;
	const float MidRightH = 145.0f;
	DrawBox(RightX, MidRightY, RightW, MidRightH, ColorNavyBg, ColorCyanBorder, 1.0f);

	DrawBox(RightX, MidRightY, RightW, 20.0f, FLinearColor(0.02f, 0.07f, 0.16f, 0.95f), FLinearColor::Transparent, 0.0f, LayerId + 2);
	FPaintGeometry KanHeadGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(RightX + 8.0f, MidRightY + 3.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, KanHeadGeom, TEXT("\u25C6 ESA KAN NEURAL NETWORK VERIFICATION"), FontButton, ESlateDrawEffect::None, ColorCyanGlow);

	float KanRowY = MidRightY + 26.0f;
	auto DrawKanDataRow = [&](const FString& Label, const FString& Value, const FLinearColor& ValCol = FLinearColor::White)
	{
		FPaintGeometry LGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(RightX + 10.0f, KanRowY)));
		FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, LGeom, Label, FontSmall, ESlateDrawEffect::None, ColorTextMuted);

		FPaintGeometry VGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(RightX + 145.0f, KanRowY)));
		FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, VGeom, Value, FontSmall, ESlateDrawEffect::None, ValCol);
		KanRowY += 16.0f;
	};

	DrawKanDataRow(TEXT("Network Architecture:"), TEXT("Kolmogorov-Arnold (KAN)"));
	DrawKanDataRow(TEXT("Feature Dimension:"), TEXT("33 Physical CDM Features"));
	DrawKanDataRow(TEXT("KAN Predicted log\u2081\u2080(Pc):"), KanPredictedRiskStr, KanStatusColor);
	DrawKanDataRow(TEXT("KAN Estimated Pc:"), KanEstimatedPcStr, KanStatusColor);
	DrawKanDataRow(TEXT("Inference Latency:"), KanLatencyStr, ColorGreen);
	DrawKanDataRow(TEXT("Dual-Model Concordance:"), DualModelConcordanceStr, ConcordanceColor);

	// -------------------------------------------------------------------------
	// Card 3C: "TRAJECTORIES LEGEND & SAFETY CLEARANCE" (Bottom-Right)
	// -------------------------------------------------------------------------
	const float BottomRightY = MidRightY + MidRightH + 8.0f;
	const float BottomRightH = 150.0f;
	DrawBox(RightX, BottomRightY, RightW, BottomRightH, ColorNavyBg, ColorCyanBorder, 1.0f);

	DrawBox(RightX, BottomRightY, RightW, 20.0f, FLinearColor(0.02f, 0.07f, 0.16f, 0.95f), FLinearColor::Transparent, 0.0f, LayerId + 2);
	FPaintGeometry TrajHeadGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(RightX + 8.0f, BottomRightY + 3.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, TrajHeadGeom, TEXT("\u25CE TRAJECTORY LEGEND & SAFETY STATUS"), FontButton, ESlateDrawEffect::None, ColorCyanGlow);

	// Nominal Cyan
	DrawBox(RightX + 10.0f, BottomRightY + 28.0f, 16.0f, 3.0f, ColorCyanGlow, FLinearColor::Transparent, 0.0f, LayerId + 3);
	FPaintGeometry NomLGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(RightX + 32.0f, BottomRightY + 23.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, NomLGeom, TEXT("Nominal Orbit (CARTOSAT-3)"), FontSmall, ESlateDrawEffect::None, FLinearColor::White);

	// Debris Amber
	DrawBox(RightX + 10.0f, BottomRightY + 44.0f, 16.0f, 3.0f, ColorAmber, FLinearColor::Transparent, 0.0f, LayerId + 3);
	FPaintGeometry DebLGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(RightX + 32.0f, BottomRightY + 39.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, DebLGeom, TEXT("Debris Fragment Orbit (SL-16 R/B)"), FontSmall, ESlateDrawEffect::None, FLinearColor::White);

	// Post-Manoeuvre Green
	DrawBox(RightX + 10.0f, BottomRightY + 60.0f, 7.0f, 3.0f, ColorGreen, FLinearColor::Transparent, 0.0f, LayerId + 3);
	DrawBox(RightX + 19.0f, BottomRightY + 60.0f, 7.0f, 3.0f, ColorGreen, FLinearColor::Transparent, 0.0f, LayerId + 3);
	FPaintGeometry PostLGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(RightX + 32.0f, BottomRightY + 55.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, PostLGeom, TEXT("Post-Manoeuvre Autonomous Orbit"), FontSmall, ESlateDrawEffect::None, FLinearColor::White);

	// Reference Shells Faint
	DrawBox(RightX + 10.0f, BottomRightY + 76.0f, 16.0f, 2.0f, FLinearColor(0.3f, 0.6f, 0.8f, 0.4f), FLinearColor::Transparent, 0.0f, LayerId + 3);
	FPaintGeometry RefLGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(RightX + 32.0f, BottomRightY + 71.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, RefLGeom, TEXT("LEO Reference Envelopes [Illustrative]"), FontSmall, ESlateDrawEffect::None, ColorTextMuted);

	// Operational Safety Status Banner
	const bool bIsSafeOp = OperationalStatusStr.Contains(TEXT("SAFE"));
	const FLinearColor OpCol = bIsSafeOp ? ColorGreen : (OperationalStatusStr.Contains(TEXT("CRITICAL")) ? ColorRed : ColorAmber);
	DrawBox(RightX + 8.0f, BottomRightY + 92.0f, RightW - 16.0f, 36.0f, bIsSafeOp ? FLinearColor(0.02f, 0.16f, 0.07f, 0.90f) : FLinearColor(0.20f, 0.04f, 0.05f, 0.90f), OpCol, 1.2f, LayerId + 2);

	FPaintGeometry OpStatGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(RightX + 14.0f, BottomRightY + 96.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, OpStatGeom, OperationalStatusStr, FontButton, ESlateDrawEffect::None, OpCol);

	FPaintGeometry OpDetGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(RightX + 14.0f, BottomRightY + 111.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, OpDetGeom, OperationalDetailStr, FontSmall, ESlateDrawEffect::None, ColorTextMuted);

	// =========================================================================
	// 4. MAIN CENTRE 3D VIEWPORT (Completely Unobstructed Centerpiece)
	// =========================================================================
	const float VpX = LeftX + LeftW + 8.0f;
	const float VpY = 58.0f;
	const float VpW = RightX - VpX - 8.0f;
	const float VpH = ScreenH - VpY - 96.0f;

	ViewportInteractionRect = FPanelRect(VpX, VpY, VpX + VpW, VpY + VpH);

	// Corner Brackets for Center 3D Viewport
	const float BracketLen = 18.0f;
	const float BracketThick = 2.0f;
	// Top-Left
	DrawBox(VpX, VpY, BracketLen, BracketThick, ColorCyanGlow, FLinearColor::Transparent, 0.0f, LayerId + 2);
	DrawBox(VpX, VpY, BracketThick, BracketLen, ColorCyanGlow, FLinearColor::Transparent, 0.0f, LayerId + 2);
	// Top-Right
	DrawBox(VpX + VpW - BracketLen, VpY, BracketLen, BracketThick, ColorCyanGlow, FLinearColor::Transparent, 0.0f, LayerId + 2);
	DrawBox(VpX + VpW - BracketThick, VpY, BracketThick, BracketLen, ColorCyanGlow, FLinearColor::Transparent, 0.0f, LayerId + 2);
	// Bottom-Left
	DrawBox(VpX, VpY + VpH - BracketThick, BracketLen, BracketThick, ColorCyanGlow, FLinearColor::Transparent, 0.0f, LayerId + 2);
	DrawBox(VpX, VpY + VpH - BracketLen, BracketThick, BracketLen, ColorCyanGlow, FLinearColor::Transparent, 0.0f, LayerId + 2);
	// Bottom-Right
	DrawBox(VpX + VpW - BracketLen, VpY + VpH - BracketThick, BracketLen, BracketThick, ColorCyanGlow, FLinearColor::Transparent, 0.0f, LayerId + 2);
	DrawBox(VpX + VpW - BracketThick, VpY + VpH - BracketLen, BracketThick, BracketLen, ColorCyanGlow, FLinearColor::Transparent, 0.0f, LayerId + 2);

	// Dynamic 3D Leader Line Callouts
	APlayerController* PC = GetOwningPlayer();
	if (!PC && GetWorld())
	{
		PC = UGameplayStatics::GetPlayerController(GetWorld(), 0);
	}
	if (PC && SimulationManager)
	{
		auto DrawWorldCallout = [&](const FVector& WorldPos, const FString& Title, const FString& Subtitle, const FLinearColor& BadgeBorderCol, const FVector2D& ScreenOffset)
		{
			FVector2D ScreenPos;
			if (PC->ProjectWorldLocationToScreen(WorldPos, ScreenPos, false))
			{
				if (ScreenPos.X >= VpX && ScreenPos.X <= (VpX + VpW) && ScreenPos.Y >= VpY && ScreenPos.Y <= (VpY + VpH))
				{
					DrawBox(ScreenPos.X - 3.0f, ScreenPos.Y - 3.0f, 6.0f, 6.0f, BadgeBorderCol, FLinearColor::White, 1.0f, LayerId + 4);

					const FVector2D BoxPos = ScreenPos + ScreenOffset;
					TArray<FVector2f> LinePoints;
					LinePoints.Add(FVector2f(ScreenPos.X, ScreenPos.Y));
					LinePoints.Add(FVector2f(BoxPos.X, BoxPos.Y + 11.0f));
					FSlateDrawElement::MakeLines(OutDrawElements, LayerId + 4, AllottedGeometry.ToPaintGeometry(), LinePoints, ESlateDrawEffect::None, BadgeBorderCol, true, 1.2f);

					const float CalloutW = 135.0f;
					const float CalloutH = 32.0f;
					DrawBox(BoxPos.X, BoxPos.Y, CalloutW, CalloutH, FLinearColor(0.01f, 0.04f, 0.10f, 0.92f), BadgeBorderCol, 1.2f, LayerId + 5);

					FPaintGeometry CTitleGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(BoxPos.X + 6.0f, BoxPos.Y + 2.0f)));
					FSlateDrawElement::MakeText(OutDrawElements, LayerId + 6, CTitleGeom, Title, FontSmall, ESlateDrawEffect::None, FLinearColor::White);

					FPaintGeometry CSubGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(BoxPos.X + 6.0f, BoxPos.Y + 15.0f)));
					FSlateDrawElement::MakeText(OutDrawElements, LayerId + 6, CSubGeom, Subtitle, FontSmall, ESlateDrawEffect::None, BadgeBorderCol);
				}
			}
		};

		if (SimulationManager->SatelliteActor)
		{
			DrawWorldCallout(SimulationManager->SatelliteActor->GetActorLocation(), TEXT("Primary Satellite"), TEXT("(SAT_PAYLOAD_01)"), ColorCyanGlow, FVector2D(-55.0, 50.0));
		}
		if (SimulationManager->DebrisActor)
		{
			DrawWorldCallout(SimulationManager->DebrisActor->GetActorLocation(), TEXT("Debris Fragment"), TEXT("(DEBRIS_PIECE_99)"), ColorAmber, FVector2D(40.0, -42.0));
		}
		if (SimulationManager->ManoeuvreVisualizer && !SimulationManager->ManoeuvreVisualizer->IsHidden())
		{
			DrawWorldCallout(SimulationManager->ManoeuvreVisualizer->GetActorLocation(), TEXT("Manoeuvre Burn"), TEXT("T + 169.63 s"), ColorGreen, FVector2D(-45.0, -42.0));
		}
		if (SimulationManager->ConjunctionVisualizer)
		{
			DrawWorldCallout(SimulationManager->ConjunctionVisualizer->GetActorLocation(), TEXT("TCA Conjunction"), TEXT("T + 903.03 s"), ColorRed, FVector2D(-35.0, -42.0));
		}
	}

	// =========================================================================
	// 4. BOTTOM AEROSPACE TIMELINE (8 Interactive Demonstration Steps)
	// =========================================================================
	const float TimeBarX = 8.0f;
	const float TimeBarY = ScreenH - 88.0f;
	const float TimeBarW = ScreenW - 16.0f;
	const float TimeBarH = 80.0f;

	DrawBox(TimeBarX, TimeBarY, TimeBarW, TimeBarH, ColorNavyBg, ColorCyanBorder, 1.2f);

	FPaintGeometry TimeHeadGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(TimeBarX + 10.0f, TimeBarY + 5.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 2, TimeHeadGeom, TEXT("\u2756 DEMONSTRATION TIMELINE (8 MILESTONES)"), FontHeader, ESlateDrawEffect::None, FLinearColor::White);

	// Summary Box on Right
	const float SumBoxW = 220.0f;
	const float SumBoxH = 66.0f;
	const float SumBoxX = TimeBarX + TimeBarW - SumBoxW - 6.0f;
	const float SumBoxY = TimeBarY + 7.0f;
	DrawBox(SumBoxX, SumBoxY, SumBoxW, SumBoxH, FLinearColor(0.02f, 0.07f, 0.16f, 0.95f), ColorCyanGlow, 1.2f, LayerId + 2);

	FPaintGeometry StepNumGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(SumBoxX + 10.0f, SumBoxY + 6.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, StepNumGeom, FString::Printf(TEXT("Current Step: %d / 8"), CurrentStepIndex), FontHeader, ESlateDrawEffect::None, FLinearColor::White);

	FPaintGeometry StepHeadGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(SumBoxX + 10.0f, SumBoxY + 28.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, StepHeadGeom, CurrentMilestoneHeadline, FontButton, ESlateDrawEffect::None, ColorGreen);

	// 8 Chevron Step Buttons
	static const TCHAR* TimelineStepNames[] = {
		TEXT("Initial Orbit\nConfig"),
		TEXT("Conjunction\nDetection"),
		TEXT("Risk\nAssessment"),
		TEXT("Manoeuvre\nPlanning"),
		TEXT("Pre-Burn\nApproach"),
		TEXT("Impulsive\nBurn"),
		TEXT("Post-Burn\nEvolution"),
		TEXT("Safe\nClearance")
	};

	const float StepAvailableW = SumBoxX - TimeBarX - 16.0f;
	const float StepButtonW = FMath::Max(65.0f, StepAvailableW / 8.0f);
	const float StepButtonH = 50.0f;
	const float StepButtonY = TimeBarY + 24.0f;

	for (int32 s = 1; s <= 8; ++s)
	{
		const float StepX = TimeBarX + 8.0f + ((s - 1) * StepButtonW);
		const bool bIsActive = (s == CurrentStepIndex);
		const bool bIsPast = (s < CurrentStepIndex);

		const int32 StepBtnId = Btn_TimelineStep1 + (s - 1);
		ButtonHitBoxes.Add(StepBtnId, FPanelRect(StepX, StepButtonY, StepX + StepButtonW - 4.0f, StepButtonY + StepButtonH));

		const bool bHover = (HoveredButtonId == StepBtnId);
		FLinearColor StepFill = bIsActive ? FLinearColor(0.04f, 0.28f, 0.12f, 0.95f) : (bIsPast ? FLinearColor(0.02f, 0.08f, 0.18f, 0.85f) : FLinearColor(0.015f, 0.04f, 0.10f, 0.85f));
		if (bHover) { StepFill = ColorHover; }

		FLinearColor StepBorder = bIsActive ? ColorGreen : (bHover ? ColorCyanGlow : (bIsPast ? FLinearColor(0.0f, 0.45f, 0.75f, 0.8f) : FLinearColor(0.12f, 0.22f, 0.35f, 0.6f)));
		DrawBox(StepX, StepButtonY, StepButtonW - 4.0f, StepButtonH, StepFill, StepBorder, bIsActive ? 2.0f : 1.0f, LayerId + 2);

		// Number Badge
		DrawBox(StepX + 5.0f, StepButtonY + 5.0f, 15.0f, 15.0f, bIsActive ? ColorGreen : FLinearColor(0.0f, 0.3f, 0.6f, 1.0f), FLinearColor::Transparent, 0.0f, LayerId + 3);
		FPaintGeometry NumGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(StepX + 9.0f, StepButtonY + 6.0f)));
		FSlateDrawElement::MakeText(OutDrawElements, LayerId + 4, NumGeom, FString::Printf(TEXT("%d"), s), FontSmall, ESlateDrawEffect::None, FLinearColor::White);

		// Label
		FPaintGeometry StepTextGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(StepX + 5.0f, StepButtonY + 22.0f)));
		FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, StepTextGeom, TimelineStepNames[s - 1], FontSmall, ESlateDrawEffect::None, bIsActive ? ColorGreen : (bHover ? FLinearColor::White : ColorTextMuted));
	}

	return LayerId + 7;
}

FReply UAvoidanceInfoPanelWidget::NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	const FVector2D MousePos = InGeometry.AbsoluteToLocal(InMouseEvent.GetScreenSpacePosition());

	// 1. Check Button Hitboxes
	if (InMouseEvent.GetEffectingButton() == EKeys::LeftMouseButton)
	{
		for (const auto& Kvp : ButtonHitBoxes)
		{
			if (Kvp.Value.Contains(MousePos))
			{
				const int32 BtnId = Kvp.Key;
				if (SimulationManager)
				{
					switch (BtnId)
					{
					case Btn_PlayPause:
						SimulationManager->TogglePlayPause();
						break;
					case Btn_Reset:
						SimulationManager->ResetSimulation();
						break;
					case Btn_StepBack:
						SimulationManager->StepBackward();
						break;
					case Btn_StepFwd:
						SimulationManager->StepForward();
						break;
					case Btn_Speed:
						SimulationManager->CycleSpeed();
						break;
					case Btn_Camera:
						SimulationManager->CycleCameraView();
						break;
					case Btn_FreeCamToggle:
						SimulationManager->ToggleFreeCamera();
						break;
					default:
						if (BtnId >= Btn_TimelineStep1 && BtnId <= Btn_TimelineStep8)
						{
							SimulationManager->JumpToStep(BtnId - Btn_TimelineStep1 + 1);
						}
						break;
					}
				}
				return FReply::Handled();
			}
		}

		// 2. Click Inside 3D Viewport
		if (ViewportInteractionRect.Contains(MousePos))
		{
			bIsOrbiting = true;
			LastMousePosition = MousePos;

			if (SimulationManager)
			{
				APlayerController* PC = UGameplayStatics::GetPlayerController(SimulationManager, 0);
				if (PC)
				{
					auto CheckPick = [&](AActor* Actor, float RadiusPx) -> bool
					{
						if (!Actor) return false;
						FVector2D ScrnPos;
						if (PC->ProjectWorldLocationToScreen(Actor->GetActorLocation(), ScrnPos, false))
						{
							return FVector2D::Distance(ScrnPos, MousePos) <= RadiusPx;
						}
						return false;
					};

					if (CheckPick(SimulationManager->SatelliteActor, 60.0f))
					{
						SimulationManager->SelectActor(SimulationManager->SatelliteActor);
					}
					else if (CheckPick(SimulationManager->DebrisActor, 50.0f))
					{
						SimulationManager->SelectActor(SimulationManager->DebrisActor);
					}
					else if (CheckPick(SimulationManager->EarthActor, 140.0f))
					{
						SimulationManager->SelectActor(SimulationManager->EarthActor);
					}
				}
			}

			return FReply::Handled().CaptureMouse(TakeWidget());
		}
	}
	else if (InMouseEvent.GetEffectingButton() == EKeys::RightMouseButton)
	{
		if (ViewportInteractionRect.Contains(MousePos))
		{
			bIsPanning = true;
			LastMousePosition = MousePos;
			return FReply::Handled().CaptureMouse(TakeWidget());
		}
	}
	else if (InMouseEvent.GetEffectingButton() == EKeys::MiddleMouseButton)
	{
		if (ViewportInteractionRect.Contains(MousePos) && SimulationManager)
		{
			SimulationManager->FrameSelectedActor();
			return FReply::Handled();
		}
	}

	return Super::NativeOnMouseButtonDown(InGeometry, InMouseEvent);
}

FReply UAvoidanceInfoPanelWidget::NativeOnMouseButtonUp(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	if (bIsOrbiting || bIsPanning)
	{
		bIsOrbiting = false;
		bIsPanning = false;
		return FReply::Handled().ReleaseMouseCapture();
	}
	return Super::NativeOnMouseButtonUp(InGeometry, InMouseEvent);
}

FReply UAvoidanceInfoPanelWidget::NativeOnMouseMove(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	const FVector2D MousePos = InGeometry.AbsoluteToLocal(InMouseEvent.GetScreenSpacePosition());

	HoveredButtonId = Btn_None;
	for (const auto& Kvp : ButtonHitBoxes)
	{
		if (Kvp.Value.Contains(MousePos))
		{
			HoveredButtonId = Kvp.Key;
			break;
		}
	}

	if (SimulationManager && SimulationManager->GetFreeCameraController())
	{
		AFreeCameraController* FreeCam = SimulationManager->GetFreeCameraController();

		if (bIsOrbiting)
		{
			const FVector2D Delta = MousePos - LastMousePosition;
			FreeCam->AddOrbitInput(static_cast<float>(Delta.Y) * 0.22f, static_cast<float>(Delta.X) * 0.22f);
			LastMousePosition = MousePos;
			return FReply::Handled();
		}
		else if (bIsPanning)
		{
			const FVector2D Delta = MousePos - LastMousePosition;
			FreeCam->AddPanInput(static_cast<float>(Delta.X), static_cast<float>(-Delta.Y));
			LastMousePosition = MousePos;
			return FReply::Handled();
		}
	}

	return Super::NativeOnMouseMove(InGeometry, InMouseEvent);
}

FReply UAvoidanceInfoPanelWidget::NativeOnMouseWheel(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	const FVector2D MousePos = InGeometry.AbsoluteToLocal(InMouseEvent.GetScreenSpacePosition());

	if (ViewportInteractionRect.Contains(MousePos) && SimulationManager && SimulationManager->GetFreeCameraController())
	{
		SimulationManager->GetFreeCameraController()->AddZoomInput(InMouseEvent.GetWheelDelta());
		return FReply::Handled();
	}

	return Super::NativeOnMouseWheel(InGeometry, InMouseEvent);
}

FCursorReply UAvoidanceInfoPanelWidget::NativeOnCursorQuery(const FGeometry& InGeometry, const FPointerEvent& InCursorEvent)
{
	if (HoveredButtonId != Btn_None)
	{
		return FCursorReply::Cursor(EMouseCursor::Hand);
	}
	if (bIsOrbiting)
	{
		return FCursorReply::Cursor(EMouseCursor::GrabHandClosed);
	}
	return FCursorReply::Cursor(EMouseCursor::Default);
}
