// Copyright Epic Games, Inc. All Rights Reserved.

#include "SatelliteAvoidanceModule.h"

#define LOCTEXT_NAMESPACE "FSatelliteAvoidanceModule"

void FSatelliteAvoidanceModule::StartupModule()
{
	UE_LOG(LogTemp, Log, TEXT("SatelliteAvoidance Module initialized for UE5."));
}

void FSatelliteAvoidanceModule::ShutdownModule()
{
	UE_LOG(LogTemp, Log, TEXT("SatelliteAvoidance Module shutdown."));
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_PRIMARY_GAME_MODULE(FSatelliteAvoidanceModule, SatelliteAvoidance, "SatelliteAvoidance");

