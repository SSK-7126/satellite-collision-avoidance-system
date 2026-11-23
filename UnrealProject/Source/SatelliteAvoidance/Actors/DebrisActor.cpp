// DebrisActor.cpp
#include "DebrisActor.h"
#include "Components/StaticMeshComponent.h"
#include "UObject/ConstructorHelpers.h"
#include "Materials/MaterialInstanceDynamic.h"

ADebrisActor::ADebrisActor()
{
	PrimaryActorTick.bCanEverTick = false;

	static ConstructorHelpers::FObjectFinder<UStaticMesh> ConeMeshFinder(TEXT("/Engine/BasicShapes/Cone.Cone"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMeshFinder(TEXT("/Engine/BasicShapes/Cube.Cube"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylMeshFinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));

	// 0. Scientific Origin Root
	SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
	RootComponent = SceneRoot;

	// 0. Visual Mesh Root (scaled independently of scientific center)
	VisualRoot = CreateDefaultSubobject<USceneComponent>(TEXT("VisualRoot"));
	VisualRoot->SetupAttachment(RootComponent);
	VisualRoot->SetRelativeScale3D(FVector(VisualMeshScale, VisualMeshScale, VisualMeshScale));

	// 1. Primary irregular jagged core
	DebrisMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("DebrisMesh"));
	DebrisMesh->SetupAttachment(VisualRoot);
	DebrisMesh->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	DebrisMesh->SetCollisionResponseToAllChannels(ECR_Ignore);
	DebrisMesh->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
	if (ConeMeshFinder.Succeeded()) { DebrisMesh->SetStaticMesh(ConeMeshFinder.Object); }
	DebrisMesh->SetRelativeScale3D(FVector(2.2, 1.6, 2.4));
	DebrisMesh->SetRelativeRotation(FRotator(35.0, 45.0, 20.0));

	// 2. Secondary Shard A (Angled facet)
	FragmentShardA = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("FragmentShardA"));
	FragmentShardA->SetupAttachment(VisualRoot);
	FragmentShardA->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (CubeMeshFinder.Succeeded()) { FragmentShardA->SetStaticMesh(CubeMeshFinder.Object); }
	FragmentShardA->SetRelativeLocation(FVector(30.0, -40.0, 30.0));
	FragmentShardA->SetRelativeRotation(FRotator(-40.0, 25.0, 60.0));
	FragmentShardA->SetRelativeScale3D(FVector(0.7, 1.8, 0.35));

	// 3. Secondary Shard B (Jagged plate)
	FragmentShardB = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("FragmentShardB"));
	FragmentShardB->SetupAttachment(VisualRoot);
	FragmentShardB->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (CubeMeshFinder.Succeeded()) { FragmentShardB->SetStaticMesh(CubeMeshFinder.Object); }
	FragmentShardB->SetRelativeLocation(FVector(-35.0, 30.0, -20.0));
	FragmentShardB->SetRelativeRotation(FRotator(30.0, -50.0, -35.0));
	FragmentShardB->SetRelativeScale3D(FVector(1.2, 0.5, 1.4));

	// 4. Torn Structural Strut
	TornStrut = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("TornStrut"));
	TornStrut->SetupAttachment(VisualRoot);
	TornStrut->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (CylMeshFinder.Succeeded()) { TornStrut->SetStaticMesh(CylMeshFinder.Object); }
	TornStrut->SetRelativeLocation(FVector(15.0, 20.0, 70.0));
	TornStrut->SetRelativeRotation(FRotator(15.0, -75.0, 40.0));
	TornStrut->SetRelativeScale3D(FVector(0.18, 0.18, 1.6));
}

void ADebrisActor::OnConstruction(const FTransform& Transform)
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

	if (DebrisMesh && VisualRoot && DebrisMesh->GetAttachParent() != VisualRoot)
	{
		DebrisMesh->AttachToComponent(VisualRoot, FAttachmentTransformRules::KeepRelativeTransform);
		DebrisMesh->SetRelativeLocationAndRotation(FVector::ZeroVector, FRotator::ZeroRotator);
	}

	UStaticMesh* ConeMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cone.Cone"));
	UStaticMesh* CubeMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
	UStaticMesh* CylMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));

	if (DebrisMesh && !DebrisMesh->GetStaticMesh() && ConeMesh) { DebrisMesh->SetStaticMesh(ConeMesh); }
	if (FragmentShardA && !FragmentShardA->GetStaticMesh() && CubeMesh) { FragmentShardA->SetStaticMesh(CubeMesh); }
	if (FragmentShardB && !FragmentShardB->GetStaticMesh() && CubeMesh) { FragmentShardB->SetStaticMesh(CubeMesh); }
	if (TornStrut && !TornStrut->GetStaticMesh() && CylMesh) { TornStrut->SetStaticMesh(CylMesh); }

	ApplyDebrisMaterials();
}

void ADebrisActor::BeginPlay()
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

	if (DebrisMesh && VisualRoot && DebrisMesh->GetAttachParent() != VisualRoot)
	{
		DebrisMesh->AttachToComponent(VisualRoot, FAttachmentTransformRules::KeepRelativeTransform);
		DebrisMesh->SetRelativeLocationAndRotation(FVector::ZeroVector, FRotator::ZeroRotator);
	}

	ApplyDebrisMaterials();
}

void ADebrisActor::ApplyDebrisMaterials()
{
	UMaterialInterface* BaseMat = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Common/M_SolidColor.M_SolidColor"));
	if (!BaseMat)
	{
		BaseMat = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
	}

	if (!BaseMat) return;

	// 1. Pitted Battered Metal Material (High-contrast metallic fragment)
	UMaterialInstanceDynamic* MetalMat = UMaterialInstanceDynamic::Create(BaseMat, this);
	if (MetalMat)
	{
		FLinearColor MetalCol = FLinearColor(0.72f, 0.70f, 0.68f, 1.0f);
		MetalMat->SetVectorParameterValue(TEXT("Color"), MetalCol);
		MetalMat->SetVectorParameterValue(TEXT("BaseColor"), MetalCol);
		MetalMat->SetScalarParameterValue(TEXT("Metallic"), 0.85f);
		MetalMat->SetScalarParameterValue(TEXT("Roughness"), 0.45f);
		MetalMat->SetScalarParameterValue(TEXT("EmissiveMultiplier"), 0.2f);
		if (DebrisMesh) { DebrisMesh->SetMaterial(0, MetalMat); }
		if (FragmentShardA) { FragmentShardA->SetMaterial(0, MetalMat); }
		if (TornStrut) { TornStrut->SetMaterial(0, MetalMat); }
	}

	// 2. High-Visibility Danger Hazard Warning Facet
	UMaterialInstanceDynamic* HazardMat = UMaterialInstanceDynamic::Create(BaseMat, this);
	if (HazardMat)
	{
		FLinearColor HazardCol = FLinearColor(1.0f, 0.35f, 0.02f, 1.0f);
		HazardMat->SetVectorParameterValue(TEXT("Color"), HazardCol);
		HazardMat->SetVectorParameterValue(TEXT("BaseColor"), HazardCol);
		HazardMat->SetScalarParameterValue(TEXT("Metallic"), 0.4f);
		HazardMat->SetScalarParameterValue(TEXT("Roughness"), 0.3f);
		HazardMat->SetScalarParameterValue(TEXT("EmissiveMultiplier"), 0.5f);
		if (FragmentShardB) { FragmentShardB->SetMaterial(0, HazardMat); }
	}
}
