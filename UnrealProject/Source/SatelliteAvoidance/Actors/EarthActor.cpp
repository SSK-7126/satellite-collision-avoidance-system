// EarthActor.cpp
#include "EarthActor.h"
#include "Components/StaticMeshComponent.h"
#include "UObject/ConstructorHelpers.h"
#include "Materials/MaterialInstanceDynamic.h"

AEarthActor::AEarthActor()
{
	PrimaryActorTick.bCanEverTick = true;

	EarthMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("EarthMesh"));
	RootComponent = EarthMesh;
	EarthMesh->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	EarthMesh->SetCollisionResponseToAllChannels(ECR_Ignore);
	EarthMesh->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMeshFinder(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	if (SphereMeshFinder.Succeeded())
	{
		EarthMesh->SetStaticMesh(SphereMeshFinder.Object);
	}

	EarthMesh->SetWorldScale3D(FVector(VisualEarthRadiusUe / 50.0)); // Default UE sphere has radius 50 cm

	AtmosphereMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("AtmosphereMesh"));
	AtmosphereMesh->SetupAttachment(RootComponent);
	AtmosphereMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (SphereMeshFinder.Succeeded())
	{
		AtmosphereMesh->SetStaticMesh(SphereMeshFinder.Object);
	}
	AtmosphereMesh->SetRelativeScale3D(FVector(AtmosphereScaleMultiplier));
}

void AEarthActor::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);

	if (EarthMesh)
	{
		if (!EarthMesh->GetStaticMesh())
		{
			UStaticMesh* SphereMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere"));
			if (SphereMesh) { EarthMesh->SetStaticMesh(SphereMesh); }
		}
		EarthMesh->SetWorldScale3D(FVector(VisualEarthRadiusUe / 50.0));
	}

	if (AtmosphereMesh)
	{
		if (!AtmosphereMesh->GetStaticMesh())
		{
			UStaticMesh* SphereMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere"));
			if (SphereMesh) { AtmosphereMesh->SetStaticMesh(SphereMesh); }
		}
		AtmosphereMesh->SetRelativeScale3D(FVector(AtmosphereScaleMultiplier));
	}

	ApplyEarthMaterials();
}

void AEarthActor::BeginPlay()
{
	Super::BeginPlay();
#if WITH_EDITOR
	SetIsSpatiallyLoaded(false);
#endif

	if (EarthMesh)
	{
		EarthMesh->SetWorldScale3D(FVector(VisualEarthRadiusUe / 50.0));
	}
	if (AtmosphereMesh)
	{
		AtmosphereMesh->SetRelativeScale3D(FVector(AtmosphereScaleMultiplier));
		AtmosphereMesh->SetVisibility(true);
		AtmosphereMesh->SetHiddenInGame(false);
	}

	ApplyEarthMaterials();
}

void AEarthActor::ApplyEarthMaterials()
{
	// 1. Realistic Earth Surface Material
	if (EarthMesh)
	{
		UMaterialInterface* BaseMat = EarthMaterial;
		if (!BaseMat)
		{
			BaseMat = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Earth/M_Earth.M_Earth"));
		}
		if (!BaseMat)
		{
			BaseMat = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
		}

		if (BaseMat)
		{
			UMaterialInstanceDynamic* EarthMat = UMaterialInstanceDynamic::Create(BaseMat, this);
			if (EarthMat)
			{
				UTexture* EarthTex = LoadObject<UTexture>(nullptr, TEXT("/Game/Earth/T_Earth_Day.T_Earth_Day"));
				if (EarthTex)
				{
					EarthMat->SetTextureParameterValue(TEXT("EarthTexture"), EarthTex);
				}
				EarthMesh->SetMaterial(0, EarthMat);
			}
		}
	}

	// 2. Subtle Translucent Blue Atmospheric Rim
	if (AtmosphereMesh)
	{
		UMaterialInterface* AtmoBase = AtmosphereMaterial;
		if (!AtmoBase)
		{
			AtmoBase = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Earth/M_Atmosphere.M_Atmosphere"));
		}

		if (AtmoBase)
		{
			UMaterialInstanceDynamic* AtmoMat = UMaterialInstanceDynamic::Create(AtmoBase, this);
			if (AtmoMat)
			{
				AtmoMat->SetVectorParameterValue(TEXT("AtmosphereColor"), FLinearColor(0.2f, 0.65f, 1.0f, 1.0f));
				AtmoMat->SetScalarParameterValue(TEXT("AtmosphereIntensity"), 2.2f);
				AtmoMat->SetScalarParameterValue(TEXT("AtmosphereFresnelExp"), 4.5f);
				AtmosphereMesh->SetMaterial(0, AtmoMat);
			}
		}
	}
}

void AEarthActor::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
	AddActorLocalRotation(FRotator(0.0, RotationRateDegPerSec * DeltaTime, 0.0));
}
