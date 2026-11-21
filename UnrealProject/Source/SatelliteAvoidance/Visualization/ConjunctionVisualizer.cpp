// ConjunctionVisualizer.cpp
#include "ConjunctionVisualizer.h"
#include "Components/StaticMeshComponent.h"
#include "UObject/ConstructorHelpers.h"
#include "Materials/MaterialInstanceDynamic.h"

AConjunctionVisualizer::AConjunctionVisualizer()
{
	PrimaryActorTick.bCanEverTick = false;

	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMeshFinder(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderMeshFinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));

	// 1. Primary Satellite TCA Marker
	TcaMarkerSphere = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("TcaMarkerSphere"));
	RootComponent = TcaMarkerSphere;
	TcaMarkerSphere->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (SphereMeshFinder.Succeeded()) { TcaMarkerSphere->SetStaticMesh(SphereMeshFinder.Object); }
	TcaMarkerSphere->SetRelativeScale3D(FVector(0.04, 0.04, 0.04));

	// 2. Secondary Debris TCA Marker
	DebrisTcaMarkerSphere = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("DebrisTcaMarkerSphere"));
	DebrisTcaMarkerSphere->SetupAttachment(RootComponent);
	DebrisTcaMarkerSphere->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (SphereMeshFinder.Succeeded()) { DebrisTcaMarkerSphere->SetStaticMesh(SphereMeshFinder.Object); }
	DebrisTcaMarkerSphere->SetRelativeScale3D(FVector(0.04, 0.04, 0.04));

	// 3. Miss Distance Connecting Line
	MissDistanceLine = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("MissDistanceLine"));
	MissDistanceLine->SetupAttachment(RootComponent);
	MissDistanceLine->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (CylinderMeshFinder.Succeeded()) { MissDistanceLine->SetStaticMesh(CylinderMeshFinder.Object); }
	MissDistanceLine->SetRelativeScale3D(FVector(0.02, 0.02, 1.0));

	// 4. Encounter Plane Disc
	EncounterPlaneDisc = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("EncounterPlaneDisc"));
	EncounterPlaneDisc->SetupAttachment(RootComponent);
	EncounterPlaneDisc->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (CylinderMeshFinder.Succeeded()) { EncounterPlaneDisc->SetStaticMesh(CylinderMeshFinder.Object); }
	EncounterPlaneDisc->SetRelativeScale3D(FVector(1.0, 1.0, 0.005));
}

void AConjunctionVisualizer::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);

	UStaticMesh* SphereMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	UStaticMesh* CylinderMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));

	if (TcaMarkerSphere && !TcaMarkerSphere->GetStaticMesh() && SphereMesh) { TcaMarkerSphere->SetStaticMesh(SphereMesh); }
	if (DebrisTcaMarkerSphere && !DebrisTcaMarkerSphere->GetStaticMesh() && SphereMesh) { DebrisTcaMarkerSphere->SetStaticMesh(SphereMesh); }
	if (MissDistanceLine && !MissDistanceLine->GetStaticMesh() && CylinderMesh) { MissDistanceLine->SetStaticMesh(CylinderMesh); }
	if (EncounterPlaneDisc && !EncounterPlaneDisc->GetStaticMesh() && CylinderMesh) { EncounterPlaneDisc->SetStaticMesh(CylinderMesh); }

	ApplyVisualizerMaterials();
}

void AConjunctionVisualizer::BeginPlay()
{
	Super::BeginPlay();
	ApplyVisualizerMaterials();
}

void AConjunctionVisualizer::ApplyVisualizerMaterials()
{
	UMaterialInterface* BaseMat = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Common/M_SolidColor.M_SolidColor"));
	if (!BaseMat)
	{
		BaseMat = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
	}

	UMaterialInterface* DiscBaseMat = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Common/M_TranslucentDisc.M_TranslucentDisc"));
	if (!DiscBaseMat)
	{
		DiscBaseMat = BaseMat;
	}

	if (!BaseMat) return;

	// 1. Primary Satellite TCA Marker (Vibrant Amber / Gold)
	if (TcaMarkerSphere)
	{
		UMaterialInstanceDynamic* TcaMat = UMaterialInstanceDynamic::Create(BaseMat, this);
		if (TcaMat)
		{
			FLinearColor TcaCol = FLinearColor(1.0f, 0.82f, 0.05f, 1.0f);
			TcaMat->SetVectorParameterValue(TEXT("Color"), TcaCol);
			TcaMat->SetVectorParameterValue(TEXT("BaseColor"), TcaCol);
			TcaMat->SetScalarParameterValue(TEXT("EmissiveMultiplier"), 1.6f);
			TcaMarkerSphere->SetMaterial(0, TcaMat);
		}
	}

	// 2. Secondary Debris TCA Marker (Hazard Red)
	if (DebrisTcaMarkerSphere)
	{
		UMaterialInstanceDynamic* DebTcaMat = UMaterialInstanceDynamic::Create(BaseMat, this);
		if (DebTcaMat)
		{
			FLinearColor DebTcaCol = FLinearColor(1.0f, 0.15f, 0.1f, 1.0f);
			DebTcaMat->SetVectorParameterValue(TEXT("Color"), DebTcaCol);
			DebTcaMat->SetVectorParameterValue(TEXT("BaseColor"), DebTcaCol);
			DebTcaMat->SetScalarParameterValue(TEXT("EmissiveMultiplier"), 1.6f);
			DebrisTcaMarkerSphere->SetMaterial(0, DebTcaMat);
		}
	}

	// 3. Miss Distance Connector (Luminous Magenta)
	if (MissDistanceLine)
	{
		UMaterialInstanceDynamic* LineMat = UMaterialInstanceDynamic::Create(BaseMat, this);
		if (LineMat)
		{
			FLinearColor LineCol = FLinearColor(1.0f, 0.05f, 0.70f, 1.0f);
			LineMat->SetVectorParameterValue(TEXT("Color"), LineCol);
			LineMat->SetVectorParameterValue(TEXT("BaseColor"), LineCol);
			LineMat->SetScalarParameterValue(TEXT("EmissiveMultiplier"), 2.0f);
			MissDistanceLine->SetMaterial(0, LineMat);
		}
	}

	// 4. Encounter Plane Disc (Translucent Violet)
	if (EncounterPlaneDisc && DiscBaseMat)
	{
		UMaterialInstanceDynamic* DiscMat = UMaterialInstanceDynamic::Create(DiscBaseMat, this);
		if (DiscMat)
		{
			FLinearColor DiscCol = FLinearColor(0.7f, 0.25f, 1.0f, 0.35f);
			DiscMat->SetVectorParameterValue(TEXT("Color"), DiscCol);
			EncounterPlaneDisc->SetMaterial(0, DiscMat);
		}
	}
}

void AConjunctionVisualizer::UpdateConjunctionGeometry(const FVector& SatTcaPos, const FVector& DebrisTcaPos, double MissDistanceUe)
{
	SetActorLocation(SatTcaPos);

	// Sphere mesh radius is 50 uu -> scale 0.018 gives 1.8 uu diameter (radius 0.9 uu)
	// For a 15.63 uu miss distance, 1.8 uu diameter marker spheres are crisp, distinct, and visible without overlapping
	const FVector MarkerScale = FVector(0.018, 0.018, 0.018);

	if (TcaMarkerSphere)
	{
		TcaMarkerSphere->SetWorldScale3D(MarkerScale);
	}

	if (DebrisTcaMarkerSphere)
	{
		DebrisTcaMarkerSphere->SetWorldLocation(DebrisTcaPos);
		DebrisTcaMarkerSphere->SetWorldScale3D(MarkerScale);
	}

	const FVector MidPoint = 0.5 * (SatTcaPos + DebrisTcaPos);
	const FVector Dir = (DebrisTcaPos - SatTcaPos);
	const double Dist = Dir.Size();

	if (Dist > 1e-4)
	{
		MissDistanceLine->SetWorldLocation(MidPoint);
		const FRotator Rot = FRotationMatrix::MakeFromZ(Dir).Rotator();
		MissDistanceLine->SetWorldRotation(Rot);
		// Cylinder default height is 100 cm, radius is 50 cm -> scale (0.006, 0.006) gives 0.6 uu diameter connector
		MissDistanceLine->SetWorldScale3D(FVector(0.006, 0.006, Dist / 100.0));

		// Center the encounter plane disc at MidPoint between both objects
		EncounterPlaneDisc->SetWorldLocation(MidPoint);
		// Disc circular face oriented obliquely to miss distance vector for 3D depth
		const FRotator DiscRot = FRotator(Rot.Pitch - 45.0f, Rot.Yaw + 35.0f, 0.0f);
		EncounterPlaneDisc->SetWorldRotation(DiscRot);
		// Disc radius 12 uu (diameter 24 uu) neatly frames the 15.63 uu encounter
		const double PlaneRadius = FMath::Clamp(Dist * 0.8, 10.0, 30.0);
		EncounterPlaneDisc->SetWorldScale3D(FVector(PlaneRadius / 50.0, PlaneRadius / 50.0, 0.002));
	}

	ApplyVisualizerMaterials();
}
