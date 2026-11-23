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

	VisualEarthRadiusUe = 26000.0;
	EarthMesh->SetWorldScale3D(FVector(VisualEarthRadiusUe / 50.0)); // Default UE sphere has radius 50 cm

	AtmosphereScaleMultiplier = 1.035;
	AtmosphereMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("AtmosphereMesh"));
	AtmosphereMesh->SetupAttachment(RootComponent);
	AtmosphereMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (SphereMeshFinder.Succeeded())
	{
		AtmosphereMesh->SetStaticMesh(SphereMeshFinder.Object);
	}
	AtmosphereMesh->SetRelativeScale3D(FVector(AtmosphereScaleMultiplier));

	StarfieldMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("StarfieldMesh"));
	StarfieldMesh->SetupAttachment(RootComponent);
	StarfieldMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	StarfieldMesh->SetCastShadow(false);
	if (SphereMeshFinder.Succeeded())
	{
		StarfieldMesh->SetStaticMesh(SphereMeshFinder.Object);
	}
	// Inverted sphere (negative scale) to render deep space starfield inward
	StarfieldMesh->SetWorldScale3D(FVector(-16000.0, -16000.0, -16000.0)); // 800,000 uu radius
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

	if (StarfieldMesh)
	{
		if (!StarfieldMesh->GetStaticMesh())
		{
			UStaticMesh* SphereMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere"));
			if (SphereMesh) { StarfieldMesh->SetStaticMesh(SphereMesh); }
		}
		StarfieldMesh->SetWorldScale3D(FVector(-16000.0, -16000.0, -16000.0));
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
	if (StarfieldMesh)
	{
		StarfieldMesh->SetWorldScale3D(FVector(-16000.0, -16000.0, -16000.0));
		StarfieldMesh->SetVisibility(true);
		StarfieldMesh->SetHiddenInGame(false);
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
			BaseMat = EarthMesh->GetMaterial(0);
		}
		if (!BaseMat)
		{
			BaseMat = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Earth/M_Earth.M_Earth"));
		}

		if (BaseMat)
		{
			UMaterialInstanceDynamic* EarthMat = Cast<UMaterialInstanceDynamic>(BaseMat);
			if (!EarthMat)
			{
				EarthMat = UMaterialInstanceDynamic::Create(BaseMat, this);
			}
			if (EarthMat)
			{
				UTexture* EarthTex = LoadObject<UTexture>(nullptr, TEXT("/Game/Earth/T_Earth_Day.T_Earth_Day"));
				if (EarthTex)
				{
					EarthMat->SetTextureParameterValue(TEXT("EarthTexture"), EarthTex);
				}
				EarthMat->SetScalarParameterValue(TEXT("Roughness"), 0.35f);
				EarthMesh->SetMaterial(0, EarthMat);
			}
		}
	}

	// 2. Luminous Translucent Cyan Atmospheric Rim
	if (AtmosphereMesh)
	{
		UMaterialInterface* AtmoBase = AtmosphereMaterial;
		if (!AtmoBase)
		{
			AtmoBase = AtmosphereMesh->GetMaterial(0);
		}
		if (!AtmoBase)
		{
			AtmoBase = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Earth/M_Atmosphere.M_Atmosphere"));
		}

		if (AtmoBase)
		{
			UMaterialInstanceDynamic* AtmoMat = Cast<UMaterialInstanceDynamic>(AtmoBase);
			if (!AtmoMat)
			{
				AtmoMat = UMaterialInstanceDynamic::Create(AtmoBase, this);
			}
			if (AtmoMat)
			{
				AtmoMat->SetVectorParameterValue(TEXT("AtmosphereColor"), FLinearColor(0.12f, 0.45f, 0.95f, 0.85f));
				AtmoMat->SetScalarParameterValue(TEXT("AtmosphereIntensity"), 1.8f);
				AtmoMat->SetScalarParameterValue(TEXT("AtmosphereFresnelExp"), 4.5f);
				AtmosphereMesh->SetMaterial(0, AtmoMat);
			}
		}
	}

	// 3. Deep Space Starfield Sphere Material
	if (StarfieldMesh)
	{
		UMaterialInterface* SkyBase = StarfieldMaterial;
		if (!SkyBase)
		{
			SkyBase = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Earth/M_SpaceSky.M_SpaceSky"));
		}
		if (!SkyBase)
		{
			SkyBase = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Common/M_SolidColor.M_SolidColor"));
		}

		if (SkyBase)
		{
			UMaterialInstanceDynamic* SkyMat = Cast<UMaterialInstanceDynamic>(SkyBase);
			if (!SkyMat)
			{
				SkyMat = UMaterialInstanceDynamic::Create(SkyBase, this);
			}
			if (SkyMat)
			{
				SkyMat->SetVectorParameterValue(TEXT("SpaceColor"), FLinearColor(0.002f, 0.004f, 0.008f, 1.0f));
				SkyMat->SetVectorParameterValue(TEXT("Color"), FLinearColor(0.002f, 0.004f, 0.008f, 1.0f));
				StarfieldMesh->SetMaterial(0, SkyMat);
			}
		}
	}
}

void AEarthActor::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
	AddActorLocalRotation(FRotator(0.0, RotationRateDegPerSec * DeltaTime, 0.0));
}
