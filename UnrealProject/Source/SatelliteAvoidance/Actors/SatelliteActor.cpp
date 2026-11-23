// SatelliteActor.cpp
#include "SatelliteActor.h"
#include "Components/StaticMeshComponent.h"
#include "UObject/ConstructorHelpers.h"
#include "Materials/MaterialInstanceDynamic.h"

ASatelliteActor::ASatelliteActor()
{
	PrimaryActorTick.bCanEverTick = false;

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMeshFinder(TEXT("/Engine/BasicShapes/Cube.Cube"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderMeshFinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> ConeMeshFinder(TEXT("/Engine/BasicShapes/Cone.Cone"));

	// 0. Scientific Origin Root
	SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
	RootComponent = SceneRoot;

	// 0. Visual Mesh Root (scaled independently of scientific center)
	VisualRoot = CreateDefaultSubobject<USceneComponent>(TEXT("VisualRoot"));
	VisualRoot->SetupAttachment(RootComponent);
	VisualRoot->SetRelativeScale3D(FVector(VisualMeshScale, VisualMeshScale, VisualMeshScale));

	// 1. Central Bus
	SatelliteBody = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SatelliteBody"));
	SatelliteBody->SetupAttachment(VisualRoot);
	SatelliteBody->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	SatelliteBody->SetCollisionResponseToAllChannels(ECR_Ignore);
	SatelliteBody->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
	if (CubeMeshFinder.Succeeded()) { SatelliteBody->SetStaticMesh(CubeMeshFinder.Object); }
	SatelliteBody->SetRelativeScale3D(FVector(2.0, 2.0, 2.2));

	// 2. Payload Deck
	PayloadDeck = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PayloadDeck"));
	PayloadDeck->SetupAttachment(VisualRoot);
	PayloadDeck->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (CubeMeshFinder.Succeeded()) { PayloadDeck->SetStaticMesh(CubeMeshFinder.Object); }
	PayloadDeck->SetRelativeLocation(FVector(0.0, 0.0, 115.0));
	PayloadDeck->SetRelativeScale3D(FVector(1.8, 1.8, 0.2));

	// 3. Earth-facing Optical Sensor
	EarthSensor = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("EarthSensor"));
	EarthSensor->SetupAttachment(PayloadDeck);
	EarthSensor->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (CylinderMeshFinder.Succeeded()) { EarthSensor->SetStaticMesh(CylinderMeshFinder.Object); }
	EarthSensor->SetRelativeLocation(FVector(0.0, 0.0, 15.0));
	EarthSensor->SetRelativeScale3D(FVector(0.65, 0.65, 0.35));

	// 4. Main Thruster Nozzle
	ThrusterNozzle = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ThrusterNozzle"));
	ThrusterNozzle->SetupAttachment(VisualRoot);
	ThrusterNozzle->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (ConeMeshFinder.Succeeded()) { ThrusterNozzle->SetStaticMesh(ConeMeshFinder.Object); }
	ThrusterNozzle->SetRelativeLocation(FVector(-105.0, 0.0, 0.0));
	ThrusterNozzle->SetRelativeRotation(FRotator(0.0, 0.0, -90.0));
	ThrusterNozzle->SetRelativeScale3D(FVector(0.7, 0.7, 0.7));

	// 5. High-Gain Antenna Mast & Dish
	AntennaMast = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("AntennaMast"));
	AntennaMast->SetupAttachment(VisualRoot);
	AntennaMast->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (CylinderMeshFinder.Succeeded()) { AntennaMast->SetStaticMesh(CylinderMeshFinder.Object); }
	AntennaMast->SetRelativeLocation(FVector(65.0, 65.0, 115.0));
	AntennaMast->SetRelativeRotation(FRotator(25.0, 45.0, 0.0));
	AntennaMast->SetRelativeScale3D(FVector(0.12, 0.12, 1.2));

	AntennaDish = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("AntennaDish"));
	AntennaDish->SetupAttachment(AntennaMast);
	AntennaDish->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (ConeMeshFinder.Succeeded()) { AntennaDish->SetStaticMesh(ConeMeshFinder.Object); }
	AntennaDish->SetRelativeLocation(FVector(0.0, 0.0, 60.0));
	AntennaDish->SetRelativeRotation(FRotator(180.0, 0.0, 0.0));
	AntennaDish->SetRelativeScale3D(FVector(1.1, 1.1, 0.3));

	// 6. Left Solar Array (Yoke + Segmented Panels)
	SolarYokeLeft = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SolarYokeLeft"));
	SolarYokeLeft->SetupAttachment(VisualRoot);
	SolarYokeLeft->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (CylinderMeshFinder.Succeeded()) { SolarYokeLeft->SetStaticMesh(CylinderMeshFinder.Object); }
	SolarYokeLeft->SetRelativeLocation(FVector(0.0, -145.0, 0.0));
	SolarYokeLeft->SetRelativeRotation(FRotator(90.0, 0.0, 0.0));
	SolarYokeLeft->SetRelativeScale3D(FVector(0.18, 0.18, 0.9));

	SolarPanelLeft = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SolarPanelLeft"));
	SolarPanelLeft->SetupAttachment(VisualRoot);
	SolarPanelLeft->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (CubeMeshFinder.Succeeded()) { SolarPanelLeft->SetStaticMesh(CubeMeshFinder.Object); }
	SolarPanelLeft->SetRelativeLocation(FVector(0.0, -290.0, 0.0));
	SolarPanelLeft->SetRelativeScale3D(FVector(1.5, 1.8, 0.08));

	SolarPanelLeft_Outboard = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SolarPanelLeft_Outboard"));
	SolarPanelLeft_Outboard->SetupAttachment(VisualRoot);
	SolarPanelLeft_Outboard->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (CubeMeshFinder.Succeeded()) { SolarPanelLeft_Outboard->SetStaticMesh(CubeMeshFinder.Object); }
	SolarPanelLeft_Outboard->SetRelativeLocation(FVector(0.0, -490.0, 0.0));
	SolarPanelLeft_Outboard->SetRelativeScale3D(FVector(1.5, 1.8, 0.08));

	// 7. Right Solar Array (Yoke + Segmented Panels)
	SolarYokeRight = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SolarYokeRight"));
	SolarYokeRight->SetupAttachment(VisualRoot);
	SolarYokeRight->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (CylinderMeshFinder.Succeeded()) { SolarYokeRight->SetStaticMesh(CylinderMeshFinder.Object); }
	SolarYokeRight->SetRelativeLocation(FVector(0.0, 145.0, 0.0));
	SolarYokeRight->SetRelativeRotation(FRotator(90.0, 0.0, 0.0));
	SolarYokeRight->SetRelativeScale3D(FVector(0.18, 0.18, 0.9));

	SolarPanelRight = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SolarPanelRight"));
	SolarPanelRight->SetupAttachment(VisualRoot);
	SolarPanelRight->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (CubeMeshFinder.Succeeded()) { SolarPanelRight->SetStaticMesh(CubeMeshFinder.Object); }
	SolarPanelRight->SetRelativeLocation(FVector(0.0, 290.0, 0.0));
	SolarPanelRight->SetRelativeScale3D(FVector(1.5, 1.8, 0.08));

	SolarPanelRight_Outboard = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SolarPanelRight_Outboard"));
	SolarPanelRight_Outboard->SetupAttachment(VisualRoot);
	SolarPanelRight_Outboard->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (CubeMeshFinder.Succeeded()) { SolarPanelRight_Outboard->SetStaticMesh(CubeMeshFinder.Object); }
	SolarPanelRight_Outboard->SetRelativeLocation(FVector(0.0, 490.0, 0.0));
	SolarPanelRight_Outboard->SetRelativeScale3D(FVector(1.5, 1.8, 0.08));
}

void ASatelliteActor::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);

	SetActorScale3D(FVector(1.0, 1.0, 1.0));
	if (SceneRoot)
	{
		SceneRoot->SetRelativeScale3D(FVector(1.0, 1.0, 1.0));
	}

	if (VisualRoot)
	{
		if (VisualRoot->GetAttachParent() != RootComponent)
		{
			VisualRoot->AttachToComponent(RootComponent, FAttachmentTransformRules::KeepRelativeTransform);
			VisualRoot->SetRelativeLocationAndRotation(FVector::ZeroVector, FRotator::ZeroRotator);
		}
		VisualRoot->SetRelativeScale3D(FVector(VisualMeshScale, VisualMeshScale, VisualMeshScale));
	}

	if (SatelliteBody && VisualRoot && SatelliteBody->GetAttachParent() != VisualRoot)
	{
		SatelliteBody->AttachToComponent(VisualRoot, FAttachmentTransformRules::KeepRelativeTransform);
		SatelliteBody->SetRelativeLocationAndRotation(FVector::ZeroVector, FRotator::ZeroRotator);
	}

	UStaticMesh* CubeMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
	UStaticMesh* CylMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	UStaticMesh* ConeMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cone.Cone"));

	if (CubeMesh)
	{
		if (SatelliteBody && !SatelliteBody->GetStaticMesh()) { SatelliteBody->SetStaticMesh(CubeMesh); }
		if (PayloadDeck && !PayloadDeck->GetStaticMesh()) { PayloadDeck->SetStaticMesh(CubeMesh); }
		if (SolarPanelLeft && !SolarPanelLeft->GetStaticMesh()) { SolarPanelLeft->SetStaticMesh(CubeMesh); }
		if (SolarPanelLeft_Outboard && !SolarPanelLeft_Outboard->GetStaticMesh()) { SolarPanelLeft_Outboard->SetStaticMesh(CubeMesh); }
		if (SolarPanelRight && !SolarPanelRight->GetStaticMesh()) { SolarPanelRight->SetStaticMesh(CubeMesh); }
		if (SolarPanelRight_Outboard && !SolarPanelRight_Outboard->GetStaticMesh()) { SolarPanelRight_Outboard->SetStaticMesh(CubeMesh); }
	}

	if (CylMesh)
	{
		if (EarthSensor && !EarthSensor->GetStaticMesh()) { EarthSensor->SetStaticMesh(CylMesh); }
		if (AntennaMast && !AntennaMast->GetStaticMesh()) { AntennaMast->SetStaticMesh(CylMesh); }
		if (SolarYokeLeft && !SolarYokeLeft->GetStaticMesh()) { SolarYokeLeft->SetStaticMesh(CylMesh); }
		if (SolarYokeRight && !SolarYokeRight->GetStaticMesh()) { SolarYokeRight->SetStaticMesh(CylMesh); }
	}

	if (ConeMesh)
	{
		if (ThrusterNozzle && !ThrusterNozzle->GetStaticMesh()) { ThrusterNozzle->SetStaticMesh(ConeMesh); }
		if (AntennaDish && !AntennaDish->GetStaticMesh()) { AntennaDish->SetStaticMesh(ConeMesh); }
	}

	ApplySatelliteMaterials();
}

void ASatelliteActor::BeginPlay()
{
	Super::BeginPlay();
#if WITH_EDITOR
	SetIsSpatiallyLoaded(false);
#endif

	SetActorScale3D(FVector(1.0, 1.0, 1.0));
	if (SceneRoot)
	{
		SceneRoot->SetRelativeScale3D(FVector(1.0, 1.0, 1.0));
	}

	if (VisualRoot)
	{
		if (VisualRoot->GetAttachParent() != RootComponent)
		{
			VisualRoot->AttachToComponent(RootComponent, FAttachmentTransformRules::KeepRelativeTransform);
			VisualRoot->SetRelativeLocationAndRotation(FVector::ZeroVector, FRotator::ZeroRotator);
		}
		VisualRoot->SetRelativeScale3D(FVector(VisualMeshScale, VisualMeshScale, VisualMeshScale));
	}

	ApplySatelliteMaterials();
}

void ASatelliteActor::ApplySatelliteMaterials()
{
	UMaterialInterface* BaseMat = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Common/M_SolidColor.M_SolidColor"));
	if (!BaseMat)
	{
		BaseMat = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
	}

	if (!BaseMat) return;

	// 1. Golden Metallic Central Bus Material
	if (SatelliteBody)
	{
		UMaterialInstanceDynamic* BodyMat = UMaterialInstanceDynamic::Create(BaseMat, this);
		if (BodyMat)
		{
			FLinearColor BodyCol = FLinearColor(0.98f, 0.82f, 0.28f, 1.0f); // Gold foil default
			if (CurrentState == ESatelliteVisualState::ConjunctionAlert)
			{
				BodyCol = FLinearColor(1.0f, 0.5f, 0.05f, 1.0f); // Warning Amber
			}
			else if (CurrentState == ESatelliteVisualState::ManoeuvredFlight)
			{
				BodyCol = FLinearColor(0.1f, 0.95f, 0.45f, 1.0f); // Success Green
			}
			BodyMat->SetVectorParameterValue(TEXT("Color"), BodyCol);
			BodyMat->SetVectorParameterValue(TEXT("BaseColor"), BodyCol);
			BodyMat->SetScalarParameterValue(TEXT("Metallic"), 0.9f);
			BodyMat->SetScalarParameterValue(TEXT("Roughness"), 0.2f);
			BodyMat->SetScalarParameterValue(TEXT("EmissiveMultiplier"), 0.35f);
			SatelliteBody->SetMaterial(0, BodyMat);
		}
	}

	// 2. Solar Panels Material (Dark Blue Photovoltaic Cells)
	UMaterialInstanceDynamic* PanelMat = UMaterialInstanceDynamic::Create(BaseMat, this);
	if (PanelMat)
	{
		FLinearColor PanelCol = FLinearColor(0.015f, 0.08f, 0.45f, 1.0f);
		PanelMat->SetVectorParameterValue(TEXT("Color"), PanelCol);
		PanelMat->SetVectorParameterValue(TEXT("BaseColor"), PanelCol);
		PanelMat->SetScalarParameterValue(TEXT("Metallic"), 0.85f);
		PanelMat->SetScalarParameterValue(TEXT("Roughness"), 0.15f);
		PanelMat->SetScalarParameterValue(TEXT("EmissiveMultiplier"), 0.25f);
		if (SolarPanelLeft) { SolarPanelLeft->SetMaterial(0, PanelMat); }
		if (SolarPanelLeft_Outboard) { SolarPanelLeft_Outboard->SetMaterial(0, PanelMat); }
		if (SolarPanelRight) { SolarPanelRight->SetMaterial(0, PanelMat); }
		if (SolarPanelRight_Outboard) { SolarPanelRight_Outboard->SetMaterial(0, PanelMat); }
	}

	// 3. Aerospace Structural Metal Material (Silver/Titanium)
	UMaterialInstanceDynamic* MetalMat = UMaterialInstanceDynamic::Create(BaseMat, this);
	if (MetalMat)
	{
		FLinearColor MetalCol = FLinearColor(0.78f, 0.82f, 0.86f, 1.0f);
		MetalMat->SetVectorParameterValue(TEXT("Color"), MetalCol);
		MetalMat->SetVectorParameterValue(TEXT("BaseColor"), MetalCol);
		MetalMat->SetScalarParameterValue(TEXT("Metallic"), 0.9f);
		MetalMat->SetScalarParameterValue(TEXT("Roughness"), 0.25f);
		MetalMat->SetScalarParameterValue(TEXT("EmissiveMultiplier"), 0.2f);
		if (PayloadDeck) { PayloadDeck->SetMaterial(0, MetalMat); }
		if (SolarYokeLeft) { SolarYokeLeft->SetMaterial(0, MetalMat); }
		if (SolarYokeRight) { SolarYokeRight->SetMaterial(0, MetalMat); }
		if (AntennaMast) { AntennaMast->SetMaterial(0, MetalMat); }
		if (ThrusterNozzle) { ThrusterNozzle->SetMaterial(0, MetalMat); }
	}

	// 4. Antenna Dish Material (High-Gain Gold Mesh Reflector)
	if (AntennaDish)
	{
		UMaterialInstanceDynamic* DishMat = UMaterialInstanceDynamic::Create(BaseMat, this);
		if (DishMat)
		{
			FLinearColor DishCol = FLinearColor(0.95f, 0.88f, 0.55f, 1.0f);
			DishMat->SetVectorParameterValue(TEXT("Color"), DishCol);
			DishMat->SetVectorParameterValue(TEXT("BaseColor"), DishCol);
			DishMat->SetScalarParameterValue(TEXT("Metallic"), 0.95f);
			DishMat->SetScalarParameterValue(TEXT("Roughness"), 0.2f);
			DishMat->SetScalarParameterValue(TEXT("EmissiveMultiplier"), 0.35f);
			AntennaDish->SetMaterial(0, DishMat);
		}
	}

	// 5. Earth Sensor Optics
	if (EarthSensor)
	{
		UMaterialInstanceDynamic* SensorMat = UMaterialInstanceDynamic::Create(BaseMat, this);
		if (SensorMat)
		{
			FLinearColor SensorCol = FLinearColor(0.02f, 0.03f, 0.05f, 1.0f);
			SensorMat->SetVectorParameterValue(TEXT("Color"), SensorCol);
			SensorMat->SetVectorParameterValue(TEXT("BaseColor"), SensorCol);
			SensorMat->SetScalarParameterValue(TEXT("Metallic"), 0.1f);
			SensorMat->SetScalarParameterValue(TEXT("Roughness"), 0.1f);
			SensorMat->SetScalarParameterValue(TEXT("EmissiveMultiplier"), 0.1f);
			EarthSensor->SetMaterial(0, SensorMat);
		}
	}
}

void ASatelliteActor::SetVisualState(ESatelliteVisualState NewState)
{
	CurrentState = NewState;
	ApplySatelliteMaterials();
}
