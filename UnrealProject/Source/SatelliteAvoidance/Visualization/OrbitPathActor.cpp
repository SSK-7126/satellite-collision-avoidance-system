// OrbitPathActor.cpp
#include "OrbitPathActor.h"
#include "Materials/MaterialInstanceDynamic.h"

AOrbitPathActor::AOrbitPathActor()
{
	PrimaryActorTick.bCanEverTick = false;
#if WITH_EDITOR
	SetIsSpatiallyLoaded(false);
#endif

	TrajectorySpline = CreateDefaultSubobject<USplineComponent>(TEXT("TrajectorySpline"));
	RootComponent = TrajectorySpline;
	TrajectorySpline->SetClosedLoop(false);
	TrajectorySpline->SetMobility(EComponentMobility::Movable);
}

void AOrbitPathActor::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);

	if (TrajectorySpline && TrajectorySpline->GetNumberOfSplinePoints() > 1 && SplineMeshes.Num() == 0)
	{
		BuildSplineMeshGeometry();
	}
}

void AOrbitPathActor::SetTrajectoryPoints(const TArray<FVector>& Points, const FLinearColor& InColor)
{
	PathColor = InColor;
	ClearSplineMeshes();

	TrajectorySpline->ClearSplinePoints(false);

	for (int32 i = 0; i < Points.Num(); ++i)
	{
		TrajectorySpline->AddSplinePoint(Points[i], ESplineCoordinateSpace::World, false);
	}
	TrajectorySpline->UpdateSpline();

	BuildSplineMeshGeometry();
}

void AOrbitPathActor::ClearSplineMeshes()
{
	for (USplineMeshComponent* MeshComp : SplineMeshes)
	{
		if (MeshComp && IsValid(MeshComp))
		{
			MeshComp->DestroyComponent();
		}
	}
	SplineMeshes.Empty();
}

void AOrbitPathActor::BuildSplineMeshGeometry()
{
	const int32 NumPoints = TrajectorySpline->GetNumberOfSplinePoints();
	if (NumPoints < 2) return;

	ClearSplineMeshes();

	UStaticMesh* CylinderMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	if (!CylinderMesh) return;

	UMaterialInterface* BaseMat = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Common/M_SolidColor.M_SolidColor"));
	if (!BaseMat)
	{
		BaseMat = LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
	}

	UMaterialInstanceDynamic* DynMat = nullptr;
	if (BaseMat)
	{
		DynMat = UMaterialInstanceDynamic::Create(BaseMat, this);
		if (DynMat)
		{
			DynMat->SetVectorParameterValue(TEXT("Color"), PathColor);
			DynMat->SetVectorParameterValue(TEXT("BaseColor"), PathColor);
			DynMat->SetScalarParameterValue(TEXT("EmissiveMultiplier"), 1.8f);
		}
	}

	const float RadiusScale = PathThickness / 50.0f; // Cylinder default radius is 50 cm
	const bool bIsHidden = IsHidden();

	for (int32 i = 0; i < NumPoints - 1; ++i)
	{
		if (bIsDashed && ((i / 3) % 2 == 1))
		{
			continue; // Elegant dashed trajectory segments matching reference design
		}

		const FVector StartPos = TrajectorySpline->GetLocationAtSplinePoint(i, ESplineCoordinateSpace::World);
		const FVector StartTangent = TrajectorySpline->GetTangentAtSplinePoint(i, ESplineCoordinateSpace::World);
		const FVector EndPos = TrajectorySpline->GetLocationAtSplinePoint(i + 1, ESplineCoordinateSpace::World);
		const FVector EndTangent = TrajectorySpline->GetTangentAtSplinePoint(i + 1, ESplineCoordinateSpace::World);

		USplineMeshComponent* SplineMesh = NewObject<USplineMeshComponent>(this);
		if (SplineMesh)
		{
			SplineMesh->SetMobility(EComponentMobility::Movable);
			SplineMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			SplineMesh->SetCastShadow(false);
			SplineMesh->SetStaticMesh(CylinderMesh);
			SplineMesh->SetForwardAxis(ESplineMeshAxis::Z);
			SplineMesh->SetStartScale(FVector2D(RadiusScale, RadiusScale));
			SplineMesh->SetEndScale(FVector2D(RadiusScale, RadiusScale));
			SplineMesh->SetStartAndEnd(StartPos, StartTangent, EndPos, EndTangent);
			if (DynMat) { SplineMesh->SetMaterial(0, DynMat); }

			SplineMesh->AttachToComponent(TrajectorySpline, FAttachmentTransformRules::KeepWorldTransform);
			SplineMesh->RegisterComponentWithWorld(GetWorld());
			SplineMesh->SetHiddenInGame(bIsHidden);
			SplineMesh->SetVisibility(!bIsHidden);

			SplineMeshes.Add(SplineMesh);
		}
	}
}

void AOrbitPathActor::SetActorHiddenInGame(bool bNewHiddenInGame)
{
	Super::SetActorHiddenInGame(bNewHiddenInGame);

	for (USplineMeshComponent* MeshComp : SplineMeshes)
	{
		if (MeshComp && IsValid(MeshComp))
		{
			MeshComp->SetHiddenInGame(bNewHiddenInGame);
			MeshComp->SetVisibility(!bNewHiddenInGame);
		}
	}
}

void AOrbitPathActor::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	ClearSplineMeshes();
	Super::EndPlay(EndPlayReason);
}
