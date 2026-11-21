// SimulationDataBridge.cpp
#include "SimulationDataBridge.h"
#include "Misc/FileHelper.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

bool USimulationDataBridge::LoadSimulationPayloadFromFile(const FString& FilePath)
{
	FString JsonString;
	if (!FFileHelper::LoadFileToString(JsonString, *FilePath))
	{
		UE_LOG(LogTemp, Error, TEXT("Failed to load JSON payload from file: %s"), *FilePath);
		return false;
	}

	TSharedPtr<FJsonObject> RootObject;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonString);
	if (!FJsonSerializer::Deserialize(Reader, RootObject) || !RootObject.IsValid())
	{
		UE_LOG(LogTemp, Error, TEXT("Failed to deserialize JSON simulation payload."));
		return false;
	}

	// 1. Metadata
	const TSharedPtr<FJsonObject>* MetaObj;
	if (RootObject->TryGetObjectField(TEXT("scenario_metadata"), MetaObj))
	{
		Metadata.ScenarioId = (*MetaObj)->GetStringField(TEXT("scenario_id"));
		Metadata.EpochUtc = (*MetaObj)->GetStringField(TEXT("epoch_utc"));
		Metadata.DurationSec = (*MetaObj)->GetNumberField(TEXT("duration_sec"));
		Metadata.ScaleFactor = (*MetaObj)->GetNumberField(TEXT("scale_factor_uu_per_m"));
		Metadata.VisualScaleLabel = (*MetaObj)->GetStringField(TEXT("visual_scale_label"));
	}

	// 2. Nominal Encounter
	const TSharedPtr<FJsonObject>* NomObj;
	if (RootObject->TryGetObjectField(TEXT("nominal_encounter"), NomObj))
	{
		NominalEncounter.TcaSeconds = (*NomObj)->GetNumberField(TEXT("tca_seconds"));
		NominalEncounter.MissDistanceMetres = (*NomObj)->GetNumberField(TEXT("miss_distance_m"));
		NominalEncounter.RelativeSpeedMps = (*NomObj)->GetNumberField(TEXT("relative_speed_mps"));
		NominalEncounter.CollisionProbability = (*NomObj)->GetNumberField(TEXT("collision_probability"));
		NominalEncounter.CollisionLog10Pc = (*NomObj)->GetNumberField(TEXT("collision_log10_pc"));
		NominalEncounter.PcStatus = (*NomObj)->GetStringField(TEXT("pc_status"));
		NominalEncounter.RiskClassification = (*NomObj)->GetStringField(TEXT("risk_classification"));

		const TArray<TSharedPtr<FJsonValue>>* RelPosArr;
		if ((*NomObj)->TryGetArrayField(TEXT("relative_position_tca_ue_uu"), RelPosArr) && RelPosArr->Num() == 3)
		{
			NominalEncounter.RelativePositionUe = FVector((*RelPosArr)[0]->AsNumber(), (*RelPosArr)[1]->AsNumber(), (*RelPosArr)[2]->AsNumber());
		}
	}

	// 3. Selected Manoeuvre
	const TSharedPtr<FJsonObject>* ManObj;
	if (RootObject->TryGetObjectField(TEXT("selected_manoeuvre"), ManObj) && (*ManObj).IsValid())
	{
		SelectedManoeuvre.ManoeuvreId = (*ManObj)->GetStringField(TEXT("manoeuvre_id"));
		SelectedManoeuvre.BurnEpochSeconds = (*ManObj)->GetNumberField(TEXT("burn_epoch_seconds"));
		SelectedManoeuvre.DeltaVMagnitudeMps = (*ManObj)->GetNumberField(TEXT("delta_v_magnitude_mps"));
		SelectedManoeuvre.DirectionLabelRtn = (*ManObj)->GetStringField(TEXT("direction_label_rtn"));

		const TArray<TSharedPtr<FJsonValue>>* DvUeArr;
		if ((*ManObj)->TryGetArrayField(TEXT("delta_v_ue_uu"), DvUeArr) && DvUeArr->Num() == 3)
		{
			SelectedManoeuvre.DeltaVUe = FVector((*DvUeArr)[0]->AsNumber(), (*DvUeArr)[1]->AsNumber(), (*DvUeArr)[2]->AsNumber());
		}

		const TArray<TSharedPtr<FJsonValue>>* BurnPosArr;
		if ((*ManObj)->TryGetArrayField(TEXT("satellite_position_at_burn_ue_uu"), BurnPosArr) && BurnPosArr->Num() == 3)
		{
			SelectedManoeuvre.SatellitePositionAtBurnUe = FVector((*BurnPosArr)[0]->AsNumber(), (*BurnPosArr)[1]->AsNumber(), (*BurnPosArr)[2]->AsNumber());
		}
	}

	// 4. Post-Manoeuvre Encounter
	const TSharedPtr<FJsonObject>* PostObj;
	if (RootObject->TryGetObjectField(TEXT("post_manoeuvre_encounter"), PostObj) && (*PostObj).IsValid())
	{
		PostManoeuvreEncounter.TcaSeconds = (*PostObj)->GetNumberField(TEXT("new_tca_seconds"));
		PostManoeuvreEncounter.MissDistanceMetres = (*PostObj)->GetNumberField(TEXT("new_miss_distance_m"));
		PostManoeuvreEncounter.RelativeSpeedMps = (*PostObj)->GetNumberField(TEXT("new_relative_speed_mps"));
		PostManoeuvreEncounter.CollisionProbability = (*PostObj)->GetNumberField(TEXT("new_collision_probability"));
		PostManoeuvreEncounter.CollisionLog10Pc = (*PostObj)->GetNumberField(TEXT("new_collision_log10_pc"));
		PostManoeuvreEncounter.PcStatus = (*PostObj)->GetStringField(TEXT("pc_status"));
		PostManoeuvreEncounter.RiskClassification = (*PostObj)->GetStringField(TEXT("risk_classification"));
	}

	// 5. Time Series
	const TSharedPtr<FJsonObject>* TsObj;
	if (RootObject->TryGetObjectField(TEXT("time_series"), TsObj))
	{
		const TArray<TSharedPtr<FJsonValue>>* TimeArr;
		if ((*TsObj)->TryGetArrayField(TEXT("timestamps_sec"), TimeArr))
		{
			Timestamps.Empty();
			for (const auto& Val : *TimeArr) { Timestamps.Add(Val->AsNumber()); }
		}

		auto ParseVectorArray = [](const TSharedPtr<FJsonObject>& Obj, const FString& FieldName, TArray<FVector>& OutArr)
		{
			OutArr.Empty();
			const TArray<TSharedPtr<FJsonValue>>* Arr;
			if (Obj->TryGetArrayField(FieldName, Arr))
			{
				for (const auto& Val : *Arr)
				{
					const TArray<TSharedPtr<FJsonValue>>& Inner = Val->AsArray();
					if (Inner.Num() == 3)
					{
						OutArr.Add(FVector(Inner[0]->AsNumber(), Inner[1]->AsNumber(), Inner[2]->AsNumber()));
					}
				}
			}
		};

		ParseVectorArray(*TsObj, TEXT("satellite_nominal_positions_ue"), SatNominalPositions);
		ParseVectorArray(*TsObj, TEXT("debris_positions_ue"), DebrisPositions);
		ParseVectorArray(*TsObj, TEXT("satellite_modified_positions_ue"), SatModifiedPositions);
	}

	// 6. Demonstration Sequence
	const TArray<TSharedPtr<FJsonValue>>* SeqArr;
	if (RootObject->TryGetArrayField(TEXT("demonstration_sequence"), SeqArr))
	{
		DemonstrationSequence.Empty();
		for (const auto& Val : *SeqArr)
		{
			const TSharedPtr<FJsonObject>& StepObj = Val->AsObject();
			FDemonstrationStep Step;
			Step.StepIndex = StepObj->GetIntegerField(TEXT("step"));
			Step.Identifier = StepObj->GetStringField(TEXT("identifier"));
			Step.SimulationTimeSec = StepObj->GetNumberField(TEXT("simulation_time_sec"));
			Step.Headline = StepObj->GetStringField(TEXT("headline"));
			Step.Description = StepObj->GetStringField(TEXT("description"));
			DemonstrationSequence.Add(Step);
		}
	}

	bIsDataLoaded = true;
	UE_LOG(LogTemp, Log, TEXT("Successfully loaded simulation payload: %s, duration: %.1fs, samples: %d"),
		*Metadata.ScenarioId, Metadata.DurationSec, Timestamps.Num());
	return true;
}

FVector USimulationDataBridge::GetSatellitePositionAtTime(double TimeSeconds, bool bUseModifiedTrajectory) const
{
	const TArray<FVector>& PosArray = (bUseModifiedTrajectory && SatModifiedPositions.Num() > 0)
		? SatModifiedPositions : SatNominalPositions;

	if (PosArray.Num() == 0 || Timestamps.Num() == 0)
	{
		return FVector::ZeroVector;
	}

	if (TimeSeconds <= Timestamps[0])
	{
		return PosArray[0];
	}
	if (TimeSeconds >= Timestamps.Last())
	{
		return PosArray.Last();
	}

	// Binary search for interval
	int32 Low = 0;
	int32 High = Timestamps.Num() - 1;
	while (High - Low > 1)
	{
		int32 Mid = (Low + High) / 2;
		if (Timestamps[Mid] <= TimeSeconds) { Low = Mid; }
		else { High = Mid; }
	}

	const double Alpha = (TimeSeconds - Timestamps[Low]) / FMath::Max(Timestamps[High] - Timestamps[Low], 1e-6);
	return FMath::Lerp(PosArray[Low], PosArray[High], Alpha);
}

FVector USimulationDataBridge::GetDebrisPositionAtTime(double TimeSeconds) const
{
	if (DebrisPositions.Num() == 0 || Timestamps.Num() == 0)
	{
		return FVector::ZeroVector;
	}

	if (TimeSeconds <= Timestamps[0]) { return DebrisPositions[0]; }
	if (TimeSeconds >= Timestamps.Last()) { return DebrisPositions.Last(); }

	int32 Low = 0;
	int32 High = Timestamps.Num() - 1;
	while (High - Low > 1)
	{
		int32 Mid = (Low + High) / 2;
		if (Timestamps[Mid] <= TimeSeconds) { Low = Mid; }
		else { High = Mid; }
	}

	const double Alpha = (TimeSeconds - Timestamps[Low]) / FMath::Max(Timestamps[High] - Timestamps[Low], 1e-6);
	return FMath::Lerp(DebrisPositions[Low], DebrisPositions[High], Alpha);
}

