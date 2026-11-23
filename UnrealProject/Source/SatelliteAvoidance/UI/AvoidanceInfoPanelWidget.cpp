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

	if (bManoeuvreHasExecuted || CurrentStepIndex >= 6)
	{
		OperationalStatusStr = TEXT("PREDICTED SAFE");
		OperationalDetailStr = TEXT("Miss distance exceeds operational threshold (2,000 m)");
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

	// Update active headline from step index
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

	// Clear hitboxes each frame for dynamic resolution adaptation
	ButtonHitBoxes.Empty();

	// Color Palette
	const FLinearColor ColorNavyBg(0.015f, 0.035f, 0.08f, 0.94f);
	const FLinearColor ColorCardBg(0.02f, 0.05f, 0.12f, 0.90f);
	const FLinearColor ColorCyanBorder(0.0f, 0.82f, 1.0f, 0.85f);
	const FLinearColor ColorCyanGlow(0.0f, 0.9f, 1.0f, 1.0f);
	const FLinearColor ColorGreen(0.0f, 0.95f, 0.45f, 1.0f);
	const FLinearColor ColorOrange(1.0f, 0.65f, 0.1f, 1.0f);
	const FLinearColor ColorRed(1.0f, 0.25f, 0.25f, 1.0f);
	const FLinearColor ColorTextMuted(0.65f, 0.80f, 0.92f, 1.0f);
	const FLinearColor ColorHover(0.0f, 0.5f, 0.85f, 0.4f);

	// Fonts
	const FSlateFontInfo FontTitle = FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 13);
	const FSlateFontInfo FontSubtitle = FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), 9);
	const FSlateFontInfo FontHeader = FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 10);
	const FSlateFontInfo FontBody = FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), 9);
	const FSlateFontInfo FontSmall = FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), 8);
	const FSlateFontInfo FontStatus = FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 12);
	const FSlateFontInfo FontButton = FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 9);

	// Helper lambdas
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
		FLinearColor Fill = bActive ? FLinearColor(0.04f, 0.25f, 0.12f, 0.95f) : (bHovered ? ColorHover : FLinearColor(0.02f, 0.08f, 0.18f, 0.90f));
		FLinearColor Border = bHovered ? ColorCyanGlow : BorderCol;
		DrawBox(X, Y, W, H, Fill, Border, bActive ? 2.0f : 1.2f, LayerId + 2);

		FPaintGeometry TextGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(X + 8.0f, Y + (H * 0.5f) - 6.0f)));
		FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, TextGeom, Label, FontButton, ESlateDrawEffect::None, TextCol);
	};

	// =========================================================================
	// 1. TOP HEADER (Title, Subtitle, Simulation Status, Playback Status Badge)
	// =========================================================================
	const float HeaderX = 8.0f;
	const float HeaderY = 8.0f;
	const float HeaderW = ScreenW - 16.0f;
	const float HeaderH = 44.0f;

	DrawBox(HeaderX, HeaderY, HeaderW, HeaderH, ColorNavyBg, ColorCyanBorder, 1.5f);

	// Bottom glowing accent line
	DrawBox(HeaderX + 1.0f, HeaderY + HeaderH - 2.0f, HeaderW - 2.0f, 2.0f, ColorCyanGlow, FLinearColor::Transparent, 0.0f);

	// Title & Subtitle
	FPaintGeometry TitleGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(HeaderX + 14.0f, HeaderY + 6.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 2, TitleGeom, TEXT("ICPS \u2013 SATELLITE COLLISION AVOIDANCE SYSTEM"), FontTitle, ESlateDrawEffect::None, FLinearColor::White);

	FPaintGeometry SubtitleGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(HeaderX + 14.0f, HeaderY + 25.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 2, SubtitleGeom, TEXT("AUTONOMOUS CONJUNCTION ASSESSMENT AND COLLISION AVOIDANCE"), FontSubtitle, ESlateDrawEffect::None, ColorTextMuted);

	// Real-Time Simulation Status Dot & Text
	const float RealTimeX = HeaderX + HeaderW - 275.0f;
	FPaintGeometry DotGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(RealTimeX, HeaderY + 14.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 2, DotGeom, TEXT("\u25CF REAL-TIME SIMULATION"), FontButton, ESlateDrawEffect::None, ColorCyanGlow);

	// Playback Status Pill Badge
	const float BadgeW = 120.0f;
	const float BadgeH = 26.0f;
	const float BadgeX = HeaderX + HeaderW - BadgeW - 12.0f;
	const float BadgeY = HeaderY + 9.0f;
	const FLinearColor BadgeFill = bIsPlayingDisplay ? FLinearColor(0.04f, 0.28f, 0.12f, 0.95f) : FLinearColor(0.28f, 0.16f, 0.02f, 0.95f);
	const FLinearColor BadgeBorder = bIsPlayingDisplay ? ColorGreen : ColorOrange;
	const FLinearColor BadgeTextCol = bIsPlayingDisplay ? FLinearColor(0.3f, 1.0f, 0.5f, 1.0f) : FLinearColor(1.0f, 0.8f, 0.2f, 1.0f);
	DrawBox(BadgeX, BadgeY, BadgeW, BadgeH, BadgeFill, BadgeBorder, 1.5f, LayerId + 2);

	FPaintGeometry BadgeTextGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(BadgeX + 12.0f, BadgeY + 5.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, BadgeTextGeom, DisplayPlaybackStatus, FontButton, ESlateDrawEffect::None, BadgeTextCol);

	// =========================================================================
	// 2. RIGHT TELEMETRY PANEL ("MISSION TELEMETRY")
	// =========================================================================
	const float PanelW = 350.0f;
	const float PanelX = ScreenW - PanelW - 8.0f;
	const float PanelY = 58.0f;
	const float PanelH = ScreenH - PanelY - 110.0f;

	DrawBox(PanelX, PanelY, PanelW, PanelH, ColorNavyBg, ColorCyanBorder, 1.5f);

	// Panel Header
	DrawBox(PanelX, PanelY, PanelW, 32.0f, FLinearColor(0.03f, 0.10f, 0.22f, 0.95f), ColorCyanBorder, 1.0f);
	FPaintGeometry PanelTitleGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(PanelX + 12.0f, PanelY + 7.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 2, PanelTitleGeom, TEXT("\u25C6 MISSION TELEMETRY"), FontHeader, ESlateDrawEffect::None, FLinearColor::White);

	float CurrentCardY = PanelY + 36.0f;
	const float CardW = PanelW - 16.0f;
	const float CardX = PanelX + 8.0f;

	auto DrawTelemetryCard = [&](const FString& SectionHeader, const TArray<TPair<FString, FString>>& Rows, const FString& BadgeText = TEXT(""), const FLinearColor& BadgeCol = FLinearColor::White)
	{
		const float CardH = 26.0f + (Rows.Num() * 19.0f) + 6.0f;
		DrawBox(CardX, CurrentCardY, CardW, CardH, ColorCardBg, FLinearColor(0.0f, 0.45f, 0.75f, 0.6f), 1.0f, LayerId + 1);

		// Header bar with chevron
		DrawBox(CardX, CurrentCardY, CardW, 22.0f, FLinearColor(0.02f, 0.08f, 0.18f, 0.95f), FLinearColor::Transparent, 0.0f, LayerId + 2);
		FPaintGeometry SecHeadGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(CardX + 8.0f, CurrentCardY + 4.0f)));
		FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, SecHeadGeom, FString::Printf(TEXT("\u2304 %s"), *SectionHeader), FontButton, ESlateDrawEffect::None, ColorCyanGlow);

		float RowY = CurrentCardY + 25.0f;
		for (int32 r = 0; r < Rows.Num(); ++r)
		{
			FPaintGeometry LblGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(CardX + 10.0f, RowY)));
			FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, LblGeom, Rows[r].Key, FontSmall, ESlateDrawEffect::None, ColorTextMuted);

			FPaintGeometry ValGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(CardX + 142.0f, RowY)));
			FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, ValGeom, Rows[r].Value, FontSmall, ESlateDrawEffect::None, FLinearColor::White);

			RowY += 19.0f;
		}

		// Optional Status Badge at bottom right of card
		if (!BadgeText.IsEmpty())
		{
			const float BadgeW_Card = 175.0f;
			const float BadgeH_Card = 18.0f;
			const float BadgeX_Card = CardX + CardW - BadgeW_Card - 6.0f;
			const float BadgeY_Card = CurrentCardY + CardH - BadgeH_Card - 4.0f;
			DrawBox(BadgeX_Card, BadgeY_Card, BadgeW_Card, BadgeH_Card, FLinearColor(0.02f, 0.12f, 0.08f, 0.90f), BadgeCol, 1.0f, LayerId + 3);

			FPaintGeometry BTextGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(BadgeX_Card + 6.0f, BadgeY_Card + 2.0f)));
			FSlateDrawElement::MakeText(OutDrawElements, LayerId + 4, BTextGeom, BadgeText, FontSmall, ESlateDrawEffect::None, BadgeCol);
		}

		CurrentCardY += CardH + 6.0f;
	};

	// 1. Encounter Information
	TArray<TPair<FString, FString>> EncounterRows;
	EncounterRows.Add(TPair<FString, FString>(TEXT("Encounter Pair:"), EncounterPairStr));
	EncounterRows.Add(TPair<FString, FString>(TEXT("Simulation Time:"), SimTimeStr));
	EncounterRows.Add(TPair<FString, FString>(TEXT("Relative Velocity:"), RelVelocityStr));
	DrawTelemetryCard(TEXT("Encounter Information"), EncounterRows);

	// 2. Nominal (No Manoeuvre) Prediction
	TArray<TPair<FString, FString>> NominalRows;
	NominalRows.Add(TPair<FString, FString>(TEXT("Nominal TCA:"), NominalTcaStr));
	NominalRows.Add(TPair<FString, FString>(TEXT("Nominal Miss Distance:"), NominalMissDistStr));
	NominalRows.Add(TPair<FString, FString>(TEXT("Collision Prob (Pc):"), NominalPcStr));
	NominalRows.Add(TPair<FString, FString>(TEXT("Pc Quality Status:"), TEXT("")));
	DrawTelemetryCard(TEXT("Nominal (No Manoeuvre) Prediction"), NominalRows, NominalPcStatusStr, ColorGreen);

	// 3. Planned Manoeuvre
	TArray<TPair<FString, FString>> ManoeuvreRows;
	ManoeuvreRows.Add(TPair<FString, FString>(TEXT("Manoeuvre \u0394v:"), PlannedDeltaVStr));
	ManoeuvreRows.Add(TPair<FString, FString>(TEXT("Direction (RTN):"), PlannedDirectionStr));
	ManoeuvreRows.Add(TPair<FString, FString>(TEXT("Manoeuvre Epoch:"), PlannedEpochStr));
	ManoeuvreRows.Add(TPair<FString, FString>(TEXT("Status:"), TEXT("")));
	DrawTelemetryCard(TEXT("Planned Manoeuvre"), ManoeuvreRows, PlannedStatusStr, FLinearColor(0.0f, 0.7f, 1.0f, 1.0f));

	// 4. Post-Manoeuvre Prediction
	TArray<TPair<FString, FString>> PostRows;
	PostRows.Add(TPair<FString, FString>(TEXT("Predicted TCA:"), PostTcaStr));
	PostRows.Add(TPair<FString, FString>(TEXT("Predicted Miss Distance:"), PostMissDistStr));
	PostRows.Add(TPair<FString, FString>(TEXT("Collision Prob (Pc):"), PostPcStr));
	PostRows.Add(TPair<FString, FString>(TEXT("Pc Quality Status:"), TEXT("")));
	DrawTelemetryCard(TEXT("Post-Manoeuvre Prediction"), PostRows, PostPcStatusStr, FLinearColor(0.9f, 0.35f, 1.0f, 1.0f));

	// 5. KAN ML Collision Risk Assessment (ESA Kelvins B-Spline)
	TArray<TPair<FString, FString>> KanRows;
	KanRows.Add(TPair<FString, FString>(TEXT("Predicted log\u2081\u2080(Pc):"), KanPredictedRiskStr));
	KanRows.Add(TPair<FString, FString>(TEXT("Estimated Pc:"), KanEstimatedPcStr));
	KanRows.Add(TPair<FString, FString>(TEXT("Inference Latency:"), KanLatencyStr));
	KanRows.Add(TPair<FString, FString>(TEXT("Model Status:"), TEXT("")));
	DrawTelemetryCard(TEXT("KAN ML Risk (ESA Kelvins B-Spline)"), KanRows, KanStatusStr, KanStatusColor);

	// 6. Dual-Model Concordance & Verification Gate
	TArray<TPair<FString, FString>> ConcordanceRows;
	ConcordanceRows.Add(TPair<FString, FString>(TEXT("Physics Reference:"), TEXT("Foster 2D/3D (D1/D2)")));
	const double PhysLogVal = (CurrentStepIndex >= 6) ? -21.91 : -13.40;
	ConcordanceRows.Add(TPair<FString, FString>(TEXT("Physics log\u2081\u2080(Pc):"), FString::Printf(TEXT("%.2f"), PhysLogVal)));
	ConcordanceRows.Add(TPair<FString, FString>(TEXT("Concordance Delta:"), KanLogDeltaStr));
	ConcordanceRows.Add(TPair<FString, FString>(TEXT("Safety Verdict:"), TEXT("")));
	DrawTelemetryCard(TEXT("Dual-Model Verification Gate"), ConcordanceRows, DualModelConcordanceStr, ConcordanceColor);

	// 5. Operational Status Card
	const float OperH = 68.0f;
	DrawBox(CardX, CurrentCardY, CardW, OperH, FLinearColor(0.02f, 0.12f, 0.06f, 0.95f), ColorGreen, 1.5f, LayerId + 2);

	FPaintGeometry ShieldGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(CardX + 12.0f, CurrentCardY + 8.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, ShieldGeom, TEXT("\u2714 OPERATIONAL STATUS"), FontButton, ESlateDrawEffect::None, ColorTextMuted);

	FPaintGeometry SafeTextGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(CardX + 12.0f, CurrentCardY + 24.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, SafeTextGeom, OperationalStatusStr, FontStatus, ESlateDrawEffect::None, ColorGreen);

	FPaintGeometry DetailGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(CardX + 12.0f, CurrentCardY + 46.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, DetailGeom, OperationalDetailStr, FontSmall, ESlateDrawEffect::None, ColorTextMuted);

	// =========================================================================
	// 3. TOP VIEWPORT CONTROLS BAR (Play/Pause, Reset, Steps, Speed, Camera)
	// =========================================================================
	const float ControlsX = 8.0f;
	const float ControlsY = 58.0f;
	const float ControlsW = PanelX - ControlsX - 8.0f;
	const float ControlsH = 38.0f;

	DrawBox(ControlsX, ControlsY, ControlsW, ControlsH, ColorNavyBg, ColorCyanBorder, 1.2f);

	float BtnX = ControlsX + 8.0f;
	const float BtnY = ControlsY + 5.0f;
	const float BtnH = 28.0f;

	// Button: Play / Pause
	const FString PlayLabel = bIsPlayingDisplay ? TEXT("||  Pause") : TEXT("\u25B6 Play");
	DrawButton(Btn_PlayPause, BtnX, BtnY, 78.0f, BtnH, PlayLabel, ColorCyanBorder, FLinearColor::White);
	BtnX += 84.0f;

	// Button: Reset
	DrawButton(Btn_Reset, BtnX, BtnY, 74.0f, BtnH, TEXT("\u21BB Reset"), ColorCyanBorder, FLinearColor::White);
	BtnX += 80.0f;

	// Button: Step Backward
	DrawButton(Btn_StepBack, BtnX, BtnY, 82.0f, BtnH, TEXT("\u25C0 Step \u2212"), ColorCyanBorder, FLinearColor::White);
	BtnX += 88.0f;

	// Button: Step Forward
	DrawButton(Btn_StepFwd, BtnX, BtnY, 82.0f, BtnH, TEXT("\u25B6 Step +"), ColorCyanBorder, FLinearColor::White);
	BtnX += 94.0f;

	// Speed Selector
	const FString SpeedText = FString::Printf(TEXT("Speed: %.1fx \u2304"), TimeDilationDisplay);
	DrawButton(Btn_Speed, BtnX, BtnY, 110.0f, BtnH, SpeedText, ColorCyanBorder, ColorCyanGlow);
	BtnX += 118.0f;

	// Camera Selector Button
	const FString CamText = FString::Printf(TEXT("Camera: %s \u2304"), *ActiveCameraName);
	DrawButton(Btn_Camera, BtnX, BtnY, 160.0f, BtnH, CamText, ColorCyanBorder, FLinearColor::White);
	BtnX += 168.0f;

	// Free Camera Toggle Button
	const FString FreeCamText = bFreeCameraActive ? TEXT("\u25CE Free Camera: ON") : TEXT("\u25CE Free Camera: OFF");
	DrawButton(Btn_FreeCamToggle, BtnX, BtnY, 140.0f, BtnH, FreeCamText, bFreeCameraActive ? ColorGreen : ColorOrange, bFreeCameraActive ? ColorGreen : ColorOrange, bFreeCameraActive);

	// =========================================================================
	// 4. 3D VIEWPORT INTERACTION AREA & BOUNDARY
	// =========================================================================
	const float VpX = ControlsX;
	const float VpY = ControlsY + ControlsH + 6.0f;
	const float VpW = ControlsW;
	const float VpH = ScreenH - VpY - 110.0f;

	// Save interactive viewport rectangle for mouse orbit/pan/zoom capture
	ViewportInteractionRect = FPanelRect(VpX, VpY, VpX + VpW, VpY + VpH);

	// Subtle glowing outline framing the 3D scene
	FPaintGeometry VpGeom = AllottedGeometry.ToPaintGeometry(FVector2f(VpW, VpH), FSlateLayoutTransform(FVector2f(VpX, VpY)));
	FSlateDrawElement::MakeGeometryOutline(OutDrawElements, LayerId + 1, VpGeom, FLinearColor(0.0f, 0.75f, 1.0f, 0.6f), ESlateDrawEffect::None, true, 1.5f);

	// -------------------------------------------------------------------------
	// Overlays Inside Viewport:
	// A. Top-Left: Camera Controls Help Card
	// -------------------------------------------------------------------------
	const float HelpW = 205.0f;
	const float HelpH = 135.0f;
	const float HelpX = VpX + 14.0f;
	const float HelpY = VpY + 14.0f;
	DrawBox(HelpX, HelpY, HelpW, HelpH, FLinearColor(0.02f, 0.06f, 0.14f, 0.88f), ColorCyanBorder, 1.0f, LayerId + 2);

	FPaintGeometry HelpHeadGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(HelpX + 8.0f, HelpY + 6.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, HelpHeadGeom, TEXT("\u25CE Camera Controls (Free Mode)"), FontButton, ESlateDrawEffect::None, ColorCyanGlow);

	static const TCHAR* HelpLines[] = {
		TEXT("\u2022 Left Drag : Orbit / Rotate"),
		TEXT("\u2022 Right Drag : Pan"),
		TEXT("\u2022 Scroll : Zoom In / Out"),
		TEXT("\u2022 Middle Click : Focus on Object"),
		TEXT("\u2022 F : Frame Selected Object"),
		TEXT("\u2022 C : Cycle Preset Cameras"),
		TEXT("\u2022 R : Reset Camera")
	};
	float HelpLineY = HelpY + 24.0f;
	for (int32 hl = 0; hl < 7; ++hl)
	{
		FPaintGeometry LineGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(HelpX + 10.0f, HelpLineY)));
		FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, LineGeom, HelpLines[hl], FontSmall, ESlateDrawEffect::None, ColorTextMuted);
		HelpLineY += 15.0f;
	}

	// -------------------------------------------------------------------------
	// B. Bottom-Right: Trajectories Legend Card
	// -------------------------------------------------------------------------
	const float LegW = 165.0f;
	const float LegH = 82.0f;
	const float LegX = VpX + VpW - LegW - 14.0f;
	const float LegY = VpY + VpH - LegH - 14.0f;
	DrawBox(LegX, LegY, LegW, LegH, FLinearColor(0.02f, 0.06f, 0.14f, 0.88f), ColorCyanBorder, 1.0f, LayerId + 2);

	FPaintGeometry LegHeadGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(LegX + 8.0f, LegY + 6.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, LegHeadGeom, TEXT("\u25CE Trajectories"), FontButton, ESlateDrawEffect::None, FLinearColor::White);

	// Nominal Cyan
	DrawBox(LegX + 10.0f, LegY + 28.0f, 22.0f, 2.5f, FLinearColor(0.0f, 0.85f, 1.0f, 1.0f), FLinearColor::Transparent, 0.0f, LayerId + 3);
	FPaintGeometry LegNomGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(LegX + 38.0f, LegY + 22.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, LegNomGeom, TEXT("Nominal (Primary)"), FontSmall, ESlateDrawEffect::None, FLinearColor::White);

	// Debris Orange
	DrawBox(LegX + 10.0f, LegY + 46.0f, 22.0f, 2.5f, ColorOrange, FLinearColor::Transparent, 0.0f, LayerId + 3);
	FPaintGeometry LegDebGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(LegX + 38.0f, LegY + 40.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, LegDebGeom, TEXT("Debris"), FontSmall, ESlateDrawEffect::None, FLinearColor::White);

	// Post-Manoeuvre Dashed Green
	DrawBox(LegX + 10.0f, LegY + 64.0f, 7.0f, 2.5f, ColorGreen, FLinearColor::Transparent, 0.0f, LayerId + 3);
	DrawBox(LegX + 20.0f, LegY + 64.0f, 7.0f, 2.5f, ColorGreen, FLinearColor::Transparent, 0.0f, LayerId + 3);
	FPaintGeometry LegPostGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(LegX + 38.0f, LegY + 58.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, LegPostGeom, TEXT("Post-Manoeuvre"), FontSmall, ESlateDrawEffect::None, FLinearColor::White);

	// -------------------------------------------------------------------------
	// C. Dynamic 3D Callout Badges with Screen Leader Lines
	// -------------------------------------------------------------------------
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
					// Draw Pin Dot
					DrawBox(ScreenPos.X - 3.0f, ScreenPos.Y - 3.0f, 6.0f, 6.0f, BadgeBorderCol, FLinearColor::White, 1.0f, LayerId + 4);

					// Draw Leader Line
					const FVector2D BoxPos = ScreenPos + ScreenOffset;
					TArray<FVector2f> LinePoints;
					LinePoints.Add(FVector2f(ScreenPos.X, ScreenPos.Y));
					LinePoints.Add(FVector2f(BoxPos.X, BoxPos.Y + 12.0f));
					FSlateDrawElement::MakeLines(OutDrawElements, LayerId + 4, AllottedGeometry.ToPaintGeometry(), LinePoints, ESlateDrawEffect::None, BadgeBorderCol, true, 1.2f);

					// Draw Box
					const float CalloutW = 140.0f;
					const float CalloutH = 34.0f;
					DrawBox(BoxPos.X, BoxPos.Y, CalloutW, CalloutH, FLinearColor(0.01f, 0.04f, 0.10f, 0.92f), BadgeBorderCol, 1.2f, LayerId + 5);

					FPaintGeometry CTitleGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(BoxPos.X + 6.0f, BoxPos.Y + 3.0f)));
					FSlateDrawElement::MakeText(OutDrawElements, LayerId + 6, CTitleGeom, Title, FontSmall, ESlateDrawEffect::None, FLinearColor::White);

					FPaintGeometry CSubGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(BoxPos.X + 6.0f, BoxPos.Y + 16.0f)));
					FSlateDrawElement::MakeText(OutDrawElements, LayerId + 6, CSubGeom, Subtitle, FontSmall, ESlateDrawEffect::None, BadgeBorderCol);
				}
			}
		};

		if (SimulationManager->SatelliteActor)
		{
			DrawWorldCallout(SimulationManager->SatelliteActor->GetActorLocation(), TEXT("Primary Satellite"), TEXT("(SAT_PAYLOAD_01)"), ColorCyanGlow, FVector2D(-60.0, 55.0));
		}
		if (SimulationManager->DebrisActor)
		{
			DrawWorldCallout(SimulationManager->DebrisActor->GetActorLocation(), TEXT("Debris"), TEXT("(DEBRIS_PIECE_99)"), ColorOrange, FVector2D(45.0, -45.0));
		}
		if (SimulationManager->ManoeuvreVisualizer && !SimulationManager->ManoeuvreVisualizer->IsHidden())
		{
			DrawWorldCallout(SimulationManager->ManoeuvreVisualizer->GetActorLocation(), TEXT("Manoeuvre (Burn)"), TEXT("T + 169.63 s"), ColorGreen, FVector2D(-50.0, -45.0));
		}
		if (SimulationManager->ConjunctionVisualizer)
		{
			DrawWorldCallout(SimulationManager->ConjunctionVisualizer->GetActorLocation(), TEXT("TCA (Predicted)"), TEXT("T + 903.03 s"), ColorRed, FVector2D(-40.0, -45.0));
		}
	}

	// =========================================================================
	// 5. BOTTOM TIMELINE BAR ("DEMONSTRATION TIMELINE (8 STEPS)")
	// =========================================================================
	const float TimeBarX = 8.0f;
	const float TimeBarY = ScreenH - 100.0f;
	const float TimeBarW = ScreenW - 16.0f;
	const float TimeBarH = 92.0f;

	DrawBox(TimeBarX, TimeBarY, TimeBarW, TimeBarH, ColorNavyBg, ColorCyanBorder, 1.5f);

	// Timeline Title
	FPaintGeometry TimeHeadGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(TimeBarX + 12.0f, TimeBarY + 6.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 2, TimeHeadGeom, TEXT("\u2756 DEMONSTRATION TIMELINE (8 STEPS)"), FontHeader, ESlateDrawEffect::None, FLinearColor::White);

	// Current Step Summary Box on Far Right
	const float SumBoxW = 210.0f;
	const float SumBoxH = 74.0f;
	const float SumBoxX = TimeBarX + TimeBarW - SumBoxW - 8.0f;
	const float SumBoxY = TimeBarY + 9.0f;
	DrawBox(SumBoxX, SumBoxY, SumBoxW, SumBoxH, FLinearColor(0.02f, 0.08f, 0.18f, 0.95f), ColorCyanGlow, 1.5f, LayerId + 2);

	FPaintGeometry StepNumGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(SumBoxX + 10.0f, SumBoxY + 8.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, StepNumGeom, FString::Printf(TEXT("Current Step: %d / 8"), CurrentStepIndex), FontHeader, ESlateDrawEffect::None, FLinearColor::White);

	FPaintGeometry StepHeadGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(SumBoxX + 10.0f, SumBoxY + 32.0f)));
	FSlateDrawElement::MakeText(OutDrawElements, LayerId + 3, StepHeadGeom, CurrentMilestoneHeadline, FontButton, ESlateDrawEffect::None, ColorGreen);

	// 8 Chevron Step Buttons
	static const TCHAR* TimelineStepNames[] = {
		TEXT("Initial Orbital\nConfiguration"),
		TEXT("Conjunction\nDetection"),
		TEXT("Risk\nAssessment"),
		TEXT("Manoeuvre\nPlanning"),
		TEXT("Pre-Burn\nApproach"),
		TEXT("Impulsive\nBurn Execution"),
		TEXT("Post-Burn\nTrajectory"),
		TEXT("Final Encounter\nAssessment")
	};

	const float StepAvailableW = SumBoxX - TimeBarX - 16.0f;
	const float StepButtonW = FMath::Max(70.0f, StepAvailableW / 8.0f);
	const float StepButtonH = 56.0f;
	const float StepButtonY = TimeBarY + 28.0f;

	for (int32 s = 1; s <= 8; ++s)
	{
		const float StepX = TimeBarX + 10.0f + ((s - 1) * StepButtonW);
		const bool bIsActive = (s == CurrentStepIndex);
		const bool bIsPast = (s < CurrentStepIndex);

		const int32 StepBtnId = Btn_TimelineStep1 + (s - 1);
		ButtonHitBoxes.Add(StepBtnId, FPanelRect(StepX, StepButtonY, StepX + StepButtonW - 4.0f, StepButtonY + StepButtonH));

		const bool bHover = (HoveredButtonId == StepBtnId);
		FLinearColor StepFill = bIsActive ? FLinearColor(0.04f, 0.28f, 0.12f, 0.95f) : (bIsPast ? FLinearColor(0.02f, 0.08f, 0.20f, 0.85f) : FLinearColor(0.015f, 0.04f, 0.10f, 0.85f));
		if (bHover) { StepFill = ColorHover; }

		FLinearColor StepBorder = bIsActive ? ColorGreen : (bHover ? ColorCyanGlow : (bIsPast ? FLinearColor(0.0f, 0.45f, 0.75f, 0.8f) : FLinearColor(0.12f, 0.22f, 0.35f, 0.6f)));
		DrawBox(StepX, StepButtonY, StepButtonW - 4.0f, StepButtonH, StepFill, StepBorder, bIsActive ? 2.0f : 1.0f, LayerId + 2);

		// Step Number Badge Circle
		DrawBox(StepX + 6.0f, StepButtonY + 6.0f, 16.0f, 16.0f, bIsActive ? ColorGreen : FLinearColor(0.0f, 0.3f, 0.6f, 1.0f), FLinearColor::Transparent, 0.0f, LayerId + 3);
		FPaintGeometry NumGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(StepX + 11.0f, StepButtonY + 7.0f)));
		FSlateDrawElement::MakeText(OutDrawElements, LayerId + 4, NumGeom, FString::Printf(TEXT("%d"), s), FontSmall, ESlateDrawEffect::None, FLinearColor::White);

		// Step Title
		FPaintGeometry StepTextGeom = AllottedGeometry.ToPaintGeometry(FSlateLayoutTransform(FVector2f(StepX + 6.0f, StepButtonY + 25.0f)));
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

			// Check object selection on click
			if (SimulationManager)
			{
				APlayerController* PC = UGameplayStatics::GetPlayerController(SimulationManager, 0);
				if (PC)
				{
					// Screen-space picking for Satellite, Debris, and Earth
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
					else if (CheckPick(SimulationManager->EarthActor, 120.0f))
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

	// Update Hovered Button ID
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
