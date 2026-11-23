// ManoeuvreVisualizer.cpp
#include "ManoeuvreVisualizer.h"
#include "Components/StaticMeshComponent.h"
#include "UObject/ConstructorHelpers.h"
#include "Materials/MaterialInstanceDynamic.h"

AManoeuvreVisualizer::AManoeuvreVisualizer()
{
	PrimaryActorTick.bCanEverTick = false;

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderMeshFinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> ConeMeshFinder(TEXT("/Engine/BasicShapes/Cone.Cone"));

	// 1. Burn Ring Marker (Cylinder radius 50 cm, height 100 cm)
	BurnMarkerRing = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BurnMarkerRing"));
	RootComponent = BurnMarkerRing;
	BurnMarkerRing->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (CylinderMeshFinder.Succeeded()) { BurnMarkerRing->SetStaticMesh(CylinderMeshFinder.Object); }
	BurnMarkerRing->SetRelativeScale3D(FVector(4.0, 4.0, 0.4));

	// 2. Delta-V Arrow Shaft (Cylinder)
	DeltaVArrowShaft = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("DeltaVArrowShaft"));
	DeltaVArrowShaft->SetupAttachment(RootComponent);
	DeltaVArrowShaft->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (CylinderMeshFinder.Succeeded()) { DeltaVArrowShaft->SetStaticMesh(CylinderMeshFinder.Object); }
	DeltaVArrowShaft->SetRelativeScale3D(FVector(0.3, 0.3, 10.0));

	// 3. Delta-V Arrow Cone Tip
	DeltaVArrow = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("DeltaVArrow"));
	DeltaVArrow->SetupAttachment(RootComponent);
	DeltaVArrow->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (ConeMeshFinder.Succeeded()) { DeltaVArrow->SetStaticMesh(ConeMeshFinder.Object); }
	DeltaVArrow->SetRelativeScale3D(FVector(0.8, 0.8, 3.5));
}

void AManoeuvreVisualizer::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);

	UStaticMesh* CylinderMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	UStaticMesh* ConeMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cone.Cone"));

	if (BurnMarkerRing && !BurnMarkerRing->GetStaticMesh() && CylinderMesh) { BurnMarkerRing->SetStaticMesh(CylinderMesh); }
	if (DeltaVArrowShaft && !DeltaVArrowShaft->GetStaticMesh() && CylinderMesh) { DeltaVArrowShaft->SetStaticMesh(CylinderMesh); }
	if (DeltaVArrow && !DeltaVArrow->GetStaticMesh() && ConeMesh) { DeltaVArrow->SetStaticMesh(ConeMesh); }

	ApplyVisualizerMaterials();
}

void AManoeuvreVisualizer::BeginPlay()
{
	Super::BeginPlay();
	ApplyVisualizerMaterials();
}

void AManoeuvreVisualizer::ApplyVisualizerMaterials()
{
	UMaterialInterface* BaseMat = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Common/M_SolidColor.M_SolidColor"));
	if (!BaseMat)
	{
		BaseMat = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
	}

	if (!BaseMat) return;

	// 1. Burn Ring Material (Vibrant Burn Green matching reference)
	if (BurnMarkerRing)
	{
		UMaterialInstanceDynamic* RingMat = UMaterialInstanceDynamic::Create(BaseMat, this);
		if (RingMat)
		{
			FLinearColor RingCol = FLinearColor(0.0f, 0.95f, 0.45f, 1.0f);
			RingMat->SetVectorParameterValue(TEXT("Color"), RingCol);
			RingMat->SetVectorParameterValue(TEXT("BaseColor"), RingCol);
			RingMat->SetScalarParameterValue(TEXT("EmissiveMultiplier"), 2.0f);
			BurnMarkerRing->SetMaterial(0, RingMat);
		}
	}

	// 2. Delta-V Arrow Materials (Vibrant Thrust Green)
	UMaterialInstanceDynamic* ArrowMat = UMaterialInstanceDynamic::Create(BaseMat, this);
	if (ArrowMat)
	{
		FLinearColor ArrowCol = FLinearColor(0.0f, 1.0f, 0.4f, 1.0f);
		ArrowMat->SetVectorParameterValue(TEXT("Color"), ArrowCol);
		ArrowMat->SetVectorParameterValue(TEXT("BaseColor"), ArrowCol);
		ArrowMat->SetScalarParameterValue(TEXT("EmissiveMultiplier"), 2.0f);
		if (DeltaVArrowShaft) { DeltaVArrowShaft->SetMaterial(0, ArrowMat); }
		if (DeltaVArrow) { DeltaVArrow->SetMaterial(0, ArrowMat); }
	}
}

void AManoeuvreVisualizer::SetManoeuvreGeometry(const FVector& BurnLocationUe, const FVector& DeltaVVectorUe, double DeltaVMagnitudeMps)
{
	SetActorLocation(BurnLocationUe);
	if (BurnMarkerRing)
	{
		BurnMarkerRing->SetWorldScale3D(FVector(4.0, 4.0, 0.4));
	}

	if (!DeltaVVectorUe.IsNearlyZero(1e-6))
	{
		// Direction along DeltaVVectorUe
		const FVector Direction = DeltaVVectorUe.GetSafeNormal();
		const FRotator Rot = FRotationMatrix::MakeFromZ(Direction).Rotator();

		// Scale arrow length proportional to delta-v magnitude
		const double TotalArrowLength = FMath::Clamp(DeltaVMagnitudeMps * 400.0, 800.0, 2000.0);
		const double ConeLength = 300.0;
		const double ShaftLength = FMath::Max(TotalArrowLength - ConeLength, 350.0);

		// Position shaft from 0 to ShaftLength
		if (DeltaVArrowShaft)
		{
			DeltaVArrowShaft->SetWorldRotation(Rot);
			DeltaVArrowShaft->SetWorldLocation(BurnLocationUe + Direction * (ShaftLength * 0.5));
			DeltaVArrowShaft->SetWorldScale3D(FVector(0.25, 0.25, ShaftLength / 100.0));
		}

		// Position cone tip at the end of the shaft
		if (DeltaVArrow)
		{
			DeltaVArrow->SetWorldRotation(Rot);
			DeltaVArrow->SetWorldLocation(BurnLocationUe + Direction * ShaftLength);
			DeltaVArrow->SetWorldScale3D(FVector(0.6, 0.6, ConeLength / 100.0));
		}
	}

	ApplyVisualizerMaterials();
}
