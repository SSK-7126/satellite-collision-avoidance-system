// AvoidanceInfoPanelWidget.cpp
#include "AvoidanceInfoPanelWidget.h"
#include "Rendering/DrawElements.h"
#include "Rendering/DrawElementTypes.h"
#include "Styling/CoreStyle.h"
#include "Styling/AppStyle.h"
#include "Framework/Application/SlateApplication.h"

UAvoidanceInfoPanelWidget::UAvoidanceInfoPanelWidget(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	DisplaySimulationTime = TEXT("T + 000.0 s");
	DisplayObjects = TEXT("INITIALIZING...");
	DisplayTca = TEXT("DATA UNAVAILABLE");
	DisplayMissDistance = TEXT("DATA UNAVAILABLE");
	DisplayRelativeSpeed = TEXT("DATA UNAVAILABLE");
	DisplayDeltaV = TEXT("DATA UNAVAILABLE");
	DisplayBurnDirection = TEXT("DATA UNAVAILABLE");
	DisplayCollisionProbability = TEXT("DATA UNAVAILABLE");
	DisplayPcStatus = TEXT("");
	DisplayRiskComparison = TEXT("STATUS: TELEMETRY INITIALIZING");
	CurrentMilestoneHeadline = TEXT("TELEMETRY INITIALIZING");
	DisplayPlaybackStatus = TEXT("PLAYING (5.0x)");
	bIsPlayingDisplay = true;
	TimeDilationDisplay = 5.0;
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
	DisplaySimulationTime = FString::Printf(TEXT("T + %05.1f s"), CurrentTimeSeconds);
	DisplayObjects = FString::Printf(TEXT("%s vs %s"), *SatId, *DebrisId);

	if (!bManoeuvreHasExecuted)
	{
		DisplayTca = FString::Printf(TEXT("%.2f s"), Nominal.TcaSeconds);
		DisplayMissDistance = FString::Printf(TEXT("%.1f m (%.3f km)"), Nominal.MissDistanceMetres, Nominal.MissDistanceMetres / 1000.0);
		DisplayRelativeSpeed = FString::Printf(TEXT("%.3f m/s"), Nominal.RelativeSpeedMps);

		DisplayDeltaV = FString::Printf(TEXT("PLANNED: %.2f m/s"), Manoeuvre.DeltaVMagnitudeMps);
		DisplayBurnDirection = FString::Printf(TEXT("%s (at T+%.1fs)"), *Manoeuvre.DirectionLabelRtn, Manoeuvre.BurnEpochSeconds);

		if (Nominal.PcStatus == TEXT("COVARIANCE_MISSING"))
		{
			DisplayCollisionProbability = TEXT("N/A (Geometric Proxy Only)");
			DisplayPcStatus = TEXT("[COVARIANCE_MISSING]");
		}
		else if (Nominal.CollisionProbability > 0.0)
		{
			DisplayCollisionProbability = FString::Printf(TEXT("%.3e (log10: %.2f)"), Nominal.CollisionProbability, Nominal.CollisionLog10Pc);
			DisplayPcStatus = Nominal.PcStatus.IsEmpty() ? TEXT("") : FString::Printf(TEXT("[%s]"), *Nominal.PcStatus);
		}
		else
		{
			DisplayCollisionProbability = FString::Printf(TEXT("< 1.000e-300 (log10: %.2f)"), Nominal.CollisionLog10Pc);
			DisplayPcStatus = Nominal.PcStatus.IsEmpty() ? TEXT("[NUMERICAL_UNDERFLOW]") : FString::Printf(TEXT("[%s]"), *Nominal.PcStatus);
		}

		DisplayRiskComparison = TEXT("STATUS: CRITICAL CONJUNCTION RISK DETECTED");
	}
	else
	{
		DisplayTca = FString::Printf(TEXT("%.2f s (Shift: +%.1fs)"), PostManoeuvre.TcaSeconds, PostManoeuvre.TcaSeconds - Nominal.TcaSeconds);
		DisplayMissDistance = FString::Printf(TEXT("%.1f m (+%.1fm)"), PostManoeuvre.MissDistanceMetres, PostManoeuvre.MissDistanceMetres - Nominal.MissDistanceMetres);
		DisplayRelativeSpeed = FString::Printf(TEXT("%.3f m/s"), PostManoeuvre.RelativeSpeedMps);

		DisplayDeltaV = FString::Printf(TEXT("APPLIED: %.2f m/s"), Manoeuvre.DeltaVMagnitudeMps);
		DisplayBurnDirection = FString::Printf(TEXT("%s (Burn Complete)"), *Manoeuvre.DirectionLabelRtn);

		if (PostManoeuvre.PcStatus == TEXT("COVARIANCE_MISSING"))
		{
			DisplayCollisionProbability = TEXT("N/A");
			DisplayPcStatus = TEXT("[COVARIANCE_MISSING]");
		}
		else if (PostManoeuvre.CollisionProbability > 0.0)
		{
			DisplayCollisionProbability = FString::Printf(TEXT("%.3e (log10: %.2f)"), PostManoeuvre.CollisionProbability, PostManoeuvre.CollisionLog10Pc);
			DisplayPcStatus = PostManoeuvre.PcStatus.IsEmpty() ? TEXT("") : FString::Printf(TEXT("[%s]"), *PostManoeuvre.PcStatus);
		}
		else
		{
			DisplayCollisionProbability = FString::Printf(TEXT("< 1.000e-300 (log10: %.2f)"), PostManoeuvre.CollisionLog10Pc);
			DisplayPcStatus = PostManoeuvre.PcStatus.IsEmpty() ? TEXT("[NUMERICAL_UNDERFLOW]") : FString::Printf(TEXT("[%s]"), *PostManoeuvre.PcStatus);
		}

		DisplayRiskComparison = FString::Printf(TEXT("STATUS: AVOIDANCE RESOLVED (Miss Dist: +%.1fm)"), PostManoeuvre.MissDistanceMetres - Nominal.MissDistanceMetres);
	}
}

void UAvoidanceInfoPanelWidget::UpdatePlaybackControls(bool bPlaying, double InTimeDilation, int32 StepIndex, int32 TotalSteps)
{
	bIsPlayingDisplay = bPlaying;
	TimeDilationDisplay = InTimeDilation;
	if (bPlaying)
	{
		DisplayPlaybackStatus = FString::Printf(TEXT("PLAYING (%.1fx)"), InTimeDilation);
	}
	else
	{
		DisplayPlaybackStatus = TEXT("PAUSED");
	}
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

	const float PanelX = 30.0f;
	const float PanelY = 30.0f;
	const float PanelW = 560.0f;
	const float PanelH = 370.0f;

	const FSlateBrush* WhiteBrush = FCoreStyle::Get().GetBrush(TEXT("WhiteBrush"));

	// 1. Background Box (Dark space navy with subtle transparency)
	FPaintGeometry BgGeom = AllottedGeometry.ToPaintGeometry(
		FVector2f(PanelW, PanelH),
		FSlateLayoutTransform(FVector2f(PanelX, PanelY))
	);
	FSlateDrawElement::MakeBox(
		OutDrawElements,
		LayerId,
		BgGeom,
		WhiteBrush,
		ESlateDrawEffect::None,
		FLinearColor(0.01f, 0.03f, 0.08f, 0.90f)
	);

	// 2. Cyan Header Bar
	FPaintGeometry HeaderGeom = AllottedGeometry.ToPaintGeometry(
		FVector2f(PanelW, 36.0f),
		FSlateLayoutTransform(FVector2f(PanelX, PanelY))
	);
	FSlateDrawElement::MakeBox(
		OutDrawElements,
		LayerId + 1,
		HeaderGeom,
		WhiteBrush,
		ESlateDrawEffect::None,
		FLinearColor(0.0f, 0.35f, 0.65f, 0.95f)
	);

	// 3. Border Outline
	FSlateDrawElement::MakeGeometryOutline(
		OutDrawElements,
		LayerId + 1,
		BgGeom,
		FLinearColor(0.0f, 0.8f, 1.0f, 0.9f),
		ESlateDrawEffect::None,
		true,
		2.0f
	);

	// Fonts
	FSlateFontInfo TitleFont = FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 11);
	FSlateFontInfo HeaderFont = FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 10);
	FSlateFontInfo BodyFont = FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), 10);
	FSlateFontInfo FooterFont = FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 9);

	// Header Title Text
	FPaintGeometry TitleGeom = AllottedGeometry.ToPaintGeometry(
		FSlateLayoutTransform(FVector2f(PanelX + 16.0f, PanelY + 9.0f))
	);
	FSlateDrawElement::MakeText(
		OutDrawElements,
		LayerId + 2,
		TitleGeom,
		TEXT("SATELLITE COLLISION AVOIDANCE SYSTEM (ICPS)"),
		TitleFont,
		ESlateDrawEffect::None,
		FLinearColor(1.0f, 1.0f, 1.0f, 1.0f)
	);

	// Playback State Badge in Header
	const FLinearColor BadgeColor = bIsPlayingDisplay ? FLinearColor(0.2f, 1.0f, 0.4f, 1.0f) : FLinearColor(1.0f, 0.75f, 0.1f, 1.0f);
	FPaintGeometry BadgeGeom = AllottedGeometry.ToPaintGeometry(
		FSlateLayoutTransform(FVector2f(PanelX + PanelW - 130.0f, PanelY + 9.0f))
	);
	FSlateDrawElement::MakeText(
		OutDrawElements,
		LayerId + 2,
		BadgeGeom,
		DisplayPlaybackStatus,
		TitleFont,
		ESlateDrawEffect::None,
		BadgeColor
	);

	// Telemetry data rows
	float CurrentY = PanelY + 44.0f;
	const float LineSpacing = 27.0f;

	auto DrawLine = [&](const FString& Label, const FString& Value, const FLinearColor& ValColor)
	{
		FPaintGeometry LabelGeom = AllottedGeometry.ToPaintGeometry(
			FSlateLayoutTransform(FVector2f(PanelX + 16.0f, CurrentY))
		);
		FSlateDrawElement::MakeText(
			OutDrawElements,
			LayerId + 2,
			LabelGeom,
			Label,
			HeaderFont,
			ESlateDrawEffect::None,
			FLinearColor(0.65f, 0.82f, 0.95f, 1.0f)
		);

		FPaintGeometry ValGeom = AllottedGeometry.ToPaintGeometry(
			FSlateLayoutTransform(FVector2f(PanelX + 180.0f, CurrentY))
		);
		FSlateDrawElement::MakeText(
			OutDrawElements,
			LayerId + 2,
			ValGeom,
			Value,
			BodyFont,
			ESlateDrawEffect::None,
			ValColor
		);

		CurrentY += LineSpacing;
	};

	DrawLine(TEXT("Simulation Time:"), DisplaySimulationTime, FLinearColor::White);
	DrawLine(TEXT("Encounter Pair:"), DisplayObjects, FLinearColor(0.9f, 0.9f, 0.9f, 1.0f));
	DrawLine(TEXT("Nominal TCA:"), DisplayTca, FLinearColor(1.0f, 0.85f, 0.2f, 1.0f));
	DrawLine(TEXT("Miss Distance:"), DisplayMissDistance, FLinearColor(1.0f, 0.85f, 0.2f, 1.0f));
	DrawLine(TEXT("Relative Speed:"), DisplayRelativeSpeed, FLinearColor(0.3f, 0.85f, 1.0f, 1.0f));
	const FString PcDisplayStr = DisplayPcStatus.IsEmpty()
		? DisplayCollisionProbability
		: FString::Printf(TEXT("%s %s"), *DisplayCollisionProbability, *DisplayPcStatus);
	DrawLine(TEXT("Collision Prob (Pc):"), PcDisplayStr, FLinearColor(1.0f, 0.35f, 0.35f, 1.0f));
	DrawLine(TEXT("Avoidance Delta-V:"), FString::Printf(TEXT("%s | %s"), *DisplayDeltaV, *DisplayBurnDirection), FLinearColor(0.2f, 1.0f, 0.4f, 1.0f));
	DrawLine(TEXT("Safety Status:"), DisplayRiskComparison, FLinearColor(0.2f, 1.0f, 0.5f, 1.0f));
	DrawLine(TEXT("Demonstration Step:"), CurrentMilestoneHeadline, FLinearColor(1.0f, 0.95f, 0.4f, 1.0f));

	// Bottom Controls Bar (Dark slate with subtle border)
	const float ControlsBarY = PanelY + PanelH - 32.0f;
	FPaintGeometry ControlsBarGeom = AllottedGeometry.ToPaintGeometry(
		FVector2f(PanelW, 32.0f),
		FSlateLayoutTransform(FVector2f(PanelX, ControlsBarY))
	);
	FSlateDrawElement::MakeBox(
		OutDrawElements,
		LayerId + 1,
		ControlsBarGeom,
		WhiteBrush,
		ESlateDrawEffect::None,
		FLinearColor(0.02f, 0.08f, 0.16f, 0.95f)
	);

	FSlateDrawElement::MakeGeometryOutline(
		OutDrawElements,
		LayerId + 2,
		ControlsBarGeom,
		FLinearColor(0.0f, 0.6f, 0.85f, 0.6f),
		ESlateDrawEffect::None,
		true,
		1.0f
	);

	FPaintGeometry ControlsTextGeom = AllottedGeometry.ToPaintGeometry(
		FSlateLayoutTransform(FVector2f(PanelX + 14.0f, ControlsBarY + 8.0f))
	);
	FSlateDrawElement::MakeText(
		OutDrawElements,
		LayerId + 3,
		ControlsTextGeom,
		TEXT("[SPACE] Play/Pause  |  [R] Reset  |  [1-8] Steps  |  [\u2191/\u2193] Speed  |  [C] Camera  |  [\u2190/\u2192] Step"),
		FooterFont,
		ESlateDrawEffect::None,
		FLinearColor(0.55f, 0.85f, 1.0f, 0.95f)
	);

	return LayerId + 4;
}
