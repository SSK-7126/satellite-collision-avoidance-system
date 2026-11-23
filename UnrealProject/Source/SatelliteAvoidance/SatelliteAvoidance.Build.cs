// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class SatelliteAvoidance : ModuleRules
{
	public SatelliteAvoidance(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[] {
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"Json",
			"JsonUtilities",
			"UMG",
			"Slate",
			"SlateCore",
			"HTTP"
		});

		PrivateDependencyModuleNames.AddRange(new string[] { });
	}
}

