using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using BepInEx;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace SolarExpanseExtract
{
    [BepInPlugin(PluginInfo.GUID, PluginInfo.Name, PluginInfo.Version)]
    public class Plugin : BaseUnityPlugin
    {
        private Type _mgrType;
        private MethodInfo _instanceMethod;
        private string _dataDir;
        private int _extractAttempts;

        void Awake()
        {
            _dataDir = ResolveDataDir();
            Directory.CreateDirectory(_dataDir);

            Logger.LogInfo($"{PluginInfo.Name} v{PluginInfo.Version}");
            Logger.LogInfo($"  Data dir: {_dataDir}");

            try
            {
                var asm = AppDomain.CurrentDomain.GetAssemblies()
                    .FirstOrDefault(a => a.GetName().Name == "Assembly-CSharp");
                if (asm == null)
                {
                    Logger.LogError("Assembly-CSharp not loaded");
                    WriteMarker("FAIL: Assembly-CSharp not found");
                    return;
                }

                _mgrType = asm.GetType("Manager.AllScriptableObjectManager")
                    ?? FindTypeByName(asm, "AllScriptableObjectManager");
                if (_mgrType == null)
                {
                    Logger.LogError("AllScriptableObjectManager not found");
                    WriteMarker("FAIL: AllScriptableObjectManager not found");
                    return;
                }
                Logger.LogInfo($"  Manager type: {_mgrType.FullName}");

                _instanceMethod = _mgrType.GetMethod("get_Instance",
                    BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static);
                if (_instanceMethod == null && _mgrType.BaseType != null)
                    _instanceMethod = _mgrType.BaseType.GetMethod("get_Instance",
                        BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static);
                if (_instanceMethod == null)
                {
                    Logger.LogError("get_Instance not found");
                    WriteMarker("FAIL: get_Instance not found");
                    return;
                }

                SceneManager.sceneLoaded += OnSceneLoaded;
                Logger.LogInfo("  Waiting for scene load...");
            }
            catch (Exception ex)
            {
                Logger.LogError($"Awake error: {ex}");
                WriteMarker($"FAIL: {ex.Message}");
            }
        }

        void OnSceneLoaded(Scene scene, LoadSceneMode mode)
        {
            _extractAttempts++;
            try
            {
                var inst = _instanceMethod.Invoke(null, null);
                if (inst == null) return;

                ExtractAll(inst);
                SceneManager.sceneLoaded -= OnSceneLoaded;
            }
            catch (Exception ex)
            {
                Logger.LogError($"Scene {scene.name}: {ex.Message}");
                if (_extractAttempts >= 5)
                {
                    WriteMarker($"FAIL after {_extractAttempts} attempts: {ex.Message}");
                    SceneManager.sceneLoaded -= OnSceneLoaded;
                }
            }
        }

        // ===================================================================
        // Extraction
        // ===================================================================

        void ExtractAll(object manager)
        {
            Logger.LogInfo("=== EXTRACTION START ===");

            var facilities = ExtractFacilities(manager);
            var spacecraft = ExtractSpacecraft(manager);
            var launchVehicles = ExtractLaunchVehicles(manager);
            var research = ExtractResearch(manager);
            var resourceIcons = ExtractResourceIcons(manager);
            var loc = ExtractLocalization();

            // Write output files
            WriteJson("facility_costs.json", facilities.costs);
            WriteJson("spacecraft_costs.json", spacecraft.costs);
            WriteJson("launch_vehicle_costs.json", launchVehicles.costs);
            WriteJson("extracted_buildability.json", facilities.buildability);
            WriteJson("research_unlocks.json", research);
            WriteJson("facility_icons.json", facilities.icons);
            WriteJson("spacecraft_icons.json", spacecraft.icons);
            WriteJson("launch_vehicle_icons.json", launchVehicles.icons);
            WriteJson("resource_icons.json", resourceIcons);
            WriteLocNames(loc);

            Logger.LogInfo($"  Facilities:  {facilities.costs.Count}");
            // --- Research exploration ---
            var resProp = _mgrType.GetProperty("AllResearchDefinition",
                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
            if (resProp != null)
            {
                var allRes = resProp.GetValue(manager);
                if (allRes != null)
                {
                    DumpProperties(allRes, "AllResearchDefinition collection");
                    var resList = GetListProp(allRes, "List") ?? (allRes as IList);
                    if (resList != null && resList.Count > 0)
                    {
                        DumpProperties(resList[0], "First Research");
                        var unlockData = GetProp<object>(resList[0], "UnlockData");
                        if (unlockData != null)
                        {
                            DumpProperties(unlockData, "UnlockData");
                            // Also dump fields
                            var udType = unlockData.GetType();
                            Logger.LogInfo("  --- UnlockData FIELDS ---");
                            foreach (var fi in udType.GetFields(
                                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance))
                            {
                                try
                                {
                                    var v = fi.GetValue(unlockData);
                                    Logger.LogInfo($"    {fi.Name} ({fi.FieldType.Name}) = {v}");
                                }
                                catch { }
                            }
                        }
                    }
                }
            }

            Logger.LogInfo($"  Launch Vehicles: {launchVehicles.costs.Count}");
            Logger.LogInfo($"  Spacecraft:  {spacecraft.costs.Count}");
            Logger.LogInfo($"  Research:    {research.Count}");
            Logger.LogInfo($"  Loc entries: {loc.Count}");
            Logger.LogInfo("=== EXTRACTION DONE ===");

            WriteMarker("OK");
        }

        // ===================================================================
        // Facilities
        // ===================================================================

        (Dictionary<string, object> costs, Dictionary<string, object> buildability,
         Dictionary<string, string> icons)
        ExtractFacilities(object manager)
        {
            var costs = new Dictionary<string, object>();
            var buildability = new Dictionary<string, object>();
            var icons = new Dictionary<string, string>();

            var allFacProp = _mgrType.GetProperty("AllFacility",
                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
            if (allFacProp == null) return (costs, buildability, icons);

            var allFac = allFacProp.GetValue(manager);
            if (allFac == null) return (costs, buildability, icons);

            var listProp = allFac.GetType().GetProperty("List",
                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance)
                ?? allFac.GetType().GetProperty("ListNotEmpty",
                    BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
            if (listProp == null) return (costs, buildability, icons);

            var list = listProp.GetValue(allFac) as IList;
            if (list == null) return (costs, buildability, icons);

            var firstFac = true;
            foreach (var f in list)
            {
                if (f == null) continue;
                var fid = GetProp<string>(f, "ID");
                if (string.IsNullOrEmpty(fid)) continue;
                if (!fid.StartsWith("build_") && !fid.StartsWith("module_")) continue;

                // Dump first facility to discover icon/sprite properties
                if (firstFac) { DumpProperties(f, "First Facility"); firstFac = false; }



                // -- Build costs --
                var price = GetProp<object>(f, "Price");
                var resources = new Dictionary<string, double>();
                double moneyCost = 0;

                if (price != null)
                {
                    // Price has ListResources (List<ResourcePriceOne>)
                    var resList = GetListProp(price, "ListResources")
                               ?? GetListProp(price, "listResources")
                               ?? GetListProp(price, "Resources");

                    if (resList != null)
                    {
                        foreach (var rp in resList)
                        {
                            if (rp == null) continue;
                            var resId = GetProp<string>(rp, "ID");
                            var amount = GetProp<double>(rp, "Price");
                            // If resource ID not found directly, try via ResourceDefinition
                            if (string.IsNullOrEmpty(resId))
                            {
                                var resDef = GetProp<object>(rp, "ResourceDefinition");
                                if (resDef != null)
                                    resId = GetProp<string>(resDef, "ID");
                            }
                            if (!string.IsNullOrEmpty(resId) && amount > 0)
                            {
                                // Strip id_resource_ prefix
                                var key = resId.StartsWith("id_resource_")
                                    ? resId.Substring(12) : resId;
                                resources[key] = amount;
                            }
                        }
                    }

                    moneyCost = GetProp<double>(price, "BuildCost");
                }

                var buildTime = GetProp<float>(f, "TimeToBuildInDays");

                var classType = f.GetType().Name;

                costs[fid] = new Dictionary<string, object>
                {
                    ["build_time_days"] = buildTime,
                    ["resources"] = resources,
                    ["money_cost"] = moneyCost,
                    ["class_type"] = classType,
                    ["facility_type"] = GetField<int>(f, "facilityType"),
                };

                // -- Buildability flags --
                buildability[fid] = new Dictionary<string, object>
                {
                    ["facility_id"] = fid,
                    ["class_type"] = classType,
                    ["facilityType"] = GetField<int>(f, "facilityType"),
                    ["isObsolete"] = GetProp<bool>(f, "IsObsolete"),
                    ["isLocked"] = GetProp<bool>(f, "IsLocked"),
                    ["showOnUI"] = GetProp<bool>(f, "ShowOnUI"),
                };

                // -- Icon/sprite name --
                var spriteName = GetSpriteName(f);
                if (!string.IsNullOrEmpty(spriteName))
                    icons[fid] = spriteName;
            }

            return (costs, buildability, icons);
        }

        // ===================================================================
        // Spacecraft
        // ===================================================================

        (Dictionary<string, object> costs, Dictionary<string, string> icons)
        ExtractSpacecraft(object manager)
        {
            var costs = new Dictionary<string, object>();
            var icons = new Dictionary<string, string>();

            // Try all known property names for spacecraft collection
            var scCollection = GetProp<object>(manager, "AllSpacecraftType");

            if (scCollection == null)
            {
                Logger.LogWarning("Spacecraft collection not found, trying alternate paths...");
                // Try to find via the manager type's properties
                foreach (var prop in _mgrType.GetProperties(
                    BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance))
                {
                    if (prop.Name.ToLower().Contains("spacecraft"))
                    {
                        Logger.LogInfo($"  Found property: {prop.Name} ({prop.PropertyType.Name})");
                        scCollection = prop.GetValue(manager);
                        if (scCollection != null) break;
                    }
                }
            }

            if (scCollection == null) return (costs, icons);

            var list = GetListProp(scCollection, "List")
                    ?? GetListProp(scCollection, "list")
                    ?? (scCollection as IList);

            if (list == null) return (costs, icons);

            foreach (var sc in list)
            {
                if (sc == null) continue;
                var scId = GetProp<string>(sc, "NameRocketType");
                if (string.IsNullOrEmpty(scId)) continue;

                var textKey = GetProp<string>(sc, "Name");

                var price = GetProp<object>(sc, "PriceBase");
                var resources = new Dictionary<string, double>();

                if (price != null)
                {
                    var resList = GetListProp(price, "ListResources")
                               ?? GetListProp(price, "listResources")
                               ?? GetListProp(price, "Resources");
                    if (resList != null)
                    {
                        foreach (var rp in resList)
                        {
                            if (rp == null) continue;
                            var resId = GetProp<string>(rp, "ID");
                            var amount = GetProp<double>(rp, "Price");
                            // If resource ID not found directly, try via ResourceDefinition
                            if (string.IsNullOrEmpty(resId))
                            {
                                var resDef = GetProp<object>(rp, "ResourceDefinition");
                                if (resDef != null)
                                    resId = GetProp<string>(resDef, "ID");
                            }
                            if (!string.IsNullOrEmpty(resId) && amount > 0)
                            {
                                var key = resId.StartsWith("id_resource_")
                                    ? resId.Substring(12) : resId;
                                resources[key] = amount;
                            }
                        }
                    }
                }

                var buildTime = GetProp<float>(sc, "TimeToBuildInDays");
                var fakeForFacility = GetField<bool>(sc, "fakeForFacility");
                var forCycleMission = GetField<bool>(sc, "forCycleMission");
                var isLocked = GetField<bool>(sc, "isLocked");
                var lockByHelpNotUse = GetProp<object>(sc, "lockByHelpNotUse");
                var lockByHelpResearchId = "";
                if (lockByHelpNotUse != null)
                {
                    lockByHelpResearchId = GetProp<string>(lockByHelpNotUse, "ID") ?? "";
                }
                var special = GetField<object>(sc, "special")?.ToString() ?? "";
                var canBuildParameter = GetProp<object>(sc, "CanBuildParameter");
                var canBuildBy = "";
                if (canBuildParameter != null)
                    canBuildBy = GetField<object>(canBuildParameter, "canBuildBy")?.ToString() ?? "";
                var spaceCraftConstructDefault = GetProp<object>(sc, "spaceCraftConstructDefault");
                var hasConstructDefault = spaceCraftConstructDefault != null;

                Logger.LogInfo($"  SC {scId}: fakeForFacility={fakeForFacility}, forCycleMission={forCycleMission}, isLocked={isLocked}, unlockResearch={lockByHelpResearchId}, special={special}, canBuildBy={canBuildBy}, hasConstruct={hasConstructDefault}");

                costs[scId] = new Dictionary<string, object>
                {
                    ["text_key"] = textKey ?? "",
                    ["build_time_days"] = buildTime,
                    ["resources"] = resources,
                    ["fakeForFacility"] = fakeForFacility,
                    ["forCycleMission"] = forCycleMission,
                    ["isLocked"] = isLocked,
                    ["lockByHelpResearchId"] = lockByHelpResearchId,
                    ["special"] = special,
                    ["canBuildBy"] = canBuildBy,
                    ["hasConstructDefault"] = hasConstructDefault,
                };

                // -- Icon/sprite name --
                var spriteName = GetSpriteName(sc);
                if (!string.IsNullOrEmpty(spriteName))
                    icons[scId] = spriteName;
            }

            return (costs, icons);
        }

        // ===================================================================
        // Launch Vehicles
        // ===================================================================

        (Dictionary<string, object> costs, Dictionary<string, string> icons)
        ExtractLaunchVehicles(object manager)
        {
            var costs = new Dictionary<string, object>();
            var icons = new Dictionary<string, string>();

            // Try all known property names for launch vehicle collection
            object lvCollection = null;
            foreach (var name in new[] {
                "AllLaunchVehicleType", "AllLaunchVehicle", "AllLaunchVehicles",
                "AllRocket", "AllRocketType", "AllLV", "allLaunchVehicleType",
                "allRockets"
            })
            {
                lvCollection = GetProp<object>(manager, name);
                if (lvCollection != null)
                {
                    Logger.LogInfo($"  Found launch vehicle collection: {name}");
                    break;
                }
            }

            if (lvCollection == null)
            {
                Logger.LogWarning("Launch vehicle collection not found, trying alternate paths...");
                // Try to find via the manager type's properties
                foreach (var prop in _mgrType.GetProperties(
                    BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance))
                {
                    var propNameLower = prop.Name.ToLower();
                    if (propNameLower.Contains("launchvehicle") ||
                        propNameLower.Contains("launch_vehicle") ||
                        propNameLower.Contains("rocket") ||
                        propNameLower.Contains("alllv"))
                    {
                        Logger.LogInfo($"  Found property: {prop.Name} ({prop.PropertyType.Name})");
                        lvCollection = prop.GetValue(manager);
                        if (lvCollection != null) break;
                    }
                }
            }

            if (lvCollection == null) return (costs, icons);

            var list = GetListProp(lvCollection, "ListNotEmpty")
                    ?? GetListProp(lvCollection, "List")
                    ?? GetListProp(lvCollection, "list")
                    ?? (lvCollection as IList);

            if (list == null) return (costs, icons);

            Logger.LogInfo($"  Launch vehicle list count: {list.Count}");

            foreach (var lv in list)
            {
                if (lv == null) continue;

                var lvId = GetProp<string>(lv, "ID")
                        ?? GetProp<string>(lv, "NameRocketType")
                        ?? GetProp<string>(lv, "NameLaunchVehicle")
                        ?? GetProp<string>(lv, "Name");
                if (string.IsNullOrEmpty(lvId)) continue;

                var textKey = GetProp<string>(lv, "Name");

                var price = GetProp<object>(lv, "PriceBase")
                         ?? GetProp<object>(lv, "Price");
                var resources = new Dictionary<string, double>();

                if (price != null)
                {
                    var resList = GetListProp(price, "ListResources")
                               ?? GetListProp(price, "listResources")
                               ?? GetListProp(price, "Resources");
                    if (resList != null)
                    {
                        foreach (var rp in resList)
                        {
                            if (rp == null) continue;
                            var resId = GetProp<string>(rp, "ID");
                            var amount = GetProp<double>(rp, "Price");
                            // If resource ID not found directly, try via ResourceDefinition
                            if (string.IsNullOrEmpty(resId))
                            {
                                var resDef = GetProp<object>(rp, "ResourceDefinition");
                                if (resDef != null)
                                    resId = GetProp<string>(resDef, "ID");
                            }
                            if (!string.IsNullOrEmpty(resId) && amount > 0)
                            {
                                var key = resId.StartsWith("id_resource_")
                                    ? resId.Substring(12) : resId;
                                resources[key] = amount;
                            }
                        }
                    }
                }

                var buildTime = GetProp<float>(lv, "TimeToBuildInDays");
                var fakeForFacility = GetField<bool>(lv, "fakeForFacility");
                var forCycleMission = GetField<bool>(lv, "forCycleMission");
                var isLocked = GetField<bool>(lv, "isLocked");
                var lockByHelpNotUse = GetProp<object>(lv, "lockByHelpNotUse");
                var lockByHelpResearchId = "";
                if (lockByHelpNotUse != null)
                {
                    lockByHelpResearchId = GetProp<string>(lockByHelpNotUse, "ID") ?? "";
                }
                var special = GetField<object>(lv, "special")?.ToString() ?? "";
                var canBuildParameter = GetProp<object>(lv, "CanBuildParameter");
                var canBuildBy = "";
                if (canBuildParameter != null)
                    canBuildBy = GetField<object>(canBuildParameter, "canBuildBy")?.ToString() ?? "";
                var spaceCraftConstructDefault = GetProp<object>(lv, "spaceCraftConstructDefault");
                var hasConstructDefault = spaceCraftConstructDefault != null;

                Logger.LogInfo($"  LV {lvId}: fakeForFacility={fakeForFacility}, forCycleMission={forCycleMission}, isLocked={isLocked}, unlockResearch={lockByHelpResearchId}, special={special}, canBuildBy={canBuildBy}, hasConstruct={hasConstructDefault}");

                costs[lvId] = new Dictionary<string, object>
                {
                    ["text_key"] = textKey ?? "",
                    ["build_time_days"] = buildTime,
                    ["resources"] = resources,
                    ["fakeForFacility"] = fakeForFacility,
                    ["forCycleMission"] = forCycleMission,
                    ["isLocked"] = isLocked,
                    ["lockByHelpResearchId"] = lockByHelpResearchId,
                    ["special"] = special,
                    ["canBuildBy"] = canBuildBy,
                    ["hasConstructDefault"] = hasConstructDefault,
                };

                // -- Icon/sprite name --
                var spriteName = GetSpriteName(lv);
                if (!string.IsNullOrEmpty(spriteName))
                    icons[lvId] = spriteName;
            }

            return (costs, icons);
        }

        // ===================================================================
        // Resource Icons
        // ===================================================================

        Dictionary<string, string> ExtractResourceIcons(object manager)
        {
            var icons = new Dictionary<string, string>();

            // Try AllResource, AllResourceDefinition, or iterate properties
            object resCollection = null;
            foreach (var name in new[] { "AllResource", "AllResourceDefinition", "AllResources", "ResourceDefinition" })
            {
                resCollection = GetProp<object>(manager, name);
                if (resCollection != null) break;
            }

            // Fallback: scan all manager properties for anything containing "resource"
            if (resCollection == null)
            {
                foreach (var prop in _mgrType.GetProperties(
                    BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance))
                {
                    if (prop.Name.ToLower().Contains("resource"))
                    {
                        Logger.LogInfo($"  Trying resource property: {prop.Name}");
                        resCollection = prop.GetValue(manager);
                        if (resCollection != null) break;
                    }
                }
            }

            if (resCollection == null)
            {
                Logger.LogWarning("Resource collection not found");
                return icons;
            }

            var list = GetListProp(resCollection, "List")
                    ?? GetListProp(resCollection, "list")
                    ?? (resCollection as IList);

            if (list == null)
            {
                Logger.LogWarning("Resource list is null");
                return icons;
            }

            var firstRes = true;
            foreach (var r in list)
            {
                if (r == null) continue;
                if (firstRes) { DumpProperties(r, "Resource"); firstRes = false; }

                var resId = GetProp<string>(r, "ID");
                if (string.IsNullOrEmpty(resId)) continue;

                // Only extract id_resource_* entries
                if (!resId.StartsWith("id_resource_")) continue;

                var spriteName = GetSpriteName(r);
                if (!string.IsNullOrEmpty(spriteName))
                    icons[resId] = spriteName;
            }

            Logger.LogInfo($"  Resource icons: {icons.Count}");
            return icons;
        }

        // ===================================================================
        // Research
        // ===================================================================

        Dictionary<string, object> ExtractResearch(object manager)
        {
            var unlockedFacility = new List<string>();
            var unlockedVehicle = new List<string>();
            var unlockedSpacecraft = new List<string>();

            Dictionary<string, object> EmptyResult() => new Dictionary<string, object>
            {
                ["unlocked_facilities"] = new List<string>(),
                ["unlocked_vehicles"] = new List<string>(),
                ["unlocked_spacecraft"] = new List<string>(),
            };

            var allResProp = _mgrType.GetProperty("AllResearchDefinition",
                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
            if (allResProp == null)
            {
                Logger.LogWarning("ExtractResearch: property not found");
                return EmptyResult();
            }

            var allRes = allResProp.GetValue(manager);
            if (allRes == null) return EmptyResult();

            var list = GetListProp(allRes, "ListNotEmpty")
                    ?? GetListProp(allRes, "List")
                    ?? (allRes as IList);

            if (list == null) return EmptyResult();

            Logger.LogInfo($"ExtractResearch: {list.Count} items");

            // --- Build ID -> research object map for tree traversal ---
            var idToResearch = new Dictionary<string, object>();
            foreach (var r in list)
            {
                if (r == null) continue;
                var rid = GetProp<string>(r, "ID");
                if (!string.IsNullOrEmpty(rid) && !idToResearch.ContainsKey(rid))
                    idToResearch[rid] = r;
            }

            // --- Compute which research is actually in the tree ---
            var validResearchIds = ComputeValidResearch(list, idToResearch);
            int skippedOrphan = 0;
            int skippedLockedForUI = 0;

            foreach (var r in list)
            {
                if (r == null) continue;

                var rid = GetProp<string>(r, "ID");
                if (string.IsNullOrEmpty(rid) || !validResearchIds.Contains(rid))
                {
                    skippedOrphan++;
                    continue;
                }

                // Skip research hidden from UI (isLockedForUI).
                // The game sets its cost to +Infinity and hides it from the
                // research tree, making it effectively unavailable.
                if (GetProp<bool>(r, "IsLockedForUI"))
                {
                    skippedLockedForUI++;
                    continue;
                }

                var unlockList = GetProp<object>(r, "UnlockDataList");
                var unlockSingle = GetProp<object>(r, "UnlockData");

                var entries = new System.Collections.Generic.List<object>();
                if (unlockList is System.Collections.IList ulist)
                    foreach (var u in ulist) if (u != null) entries.Add(u);
                if (unlockSingle != null) entries.Add(unlockSingle);

                foreach (var ud in entries)
                {
                    // actionUnlock is a FIELD (EActionUnlock enum), not a property
                    var actionStr = GetField<object>(ud, "actionUnlock")?.ToString() ?? "";
                    var param1 = GetField<string>(ud, "parameter1");

                    if (actionStr == "UnlockFacility")
                    {
                        if (!string.IsNullOrEmpty(param1)
                            && (param1.StartsWith("build_") || param1.StartsWith("module_")))
                        {
                            unlockedFacility.Add(param1);
                        }
                    }
                    else if (actionStr == "UnlockVehicleType")
                    {
                        if (!string.IsNullOrEmpty(param1))
                        {
                            unlockedVehicle.Add(param1);
                        }
                    }
                    else if (actionStr == "UnlockSpacecraftType")
                    {
                        if (!string.IsNullOrEmpty(param1))
                        {
                            unlockedSpacecraft.Add(param1);
                        }
                    }
                }
            }

            Logger.LogInfo($"ExtractResearch: {validResearchIds.Count} in tree, {skippedOrphan} orphaned, {skippedLockedForUI} locked-for-UI (skipped)");
            Logger.LogInfo($"  Unlocks: {unlockedFacility.Count} facilities, {unlockedVehicle.Count} vehicles, {unlockedSpacecraft.Count} spacecraft");
            return new Dictionary<string, object>
            {
                ["unlocked_facilities"] = unlockedFacility,
                ["unlocked_vehicles"] = unlockedVehicle,
                ["unlocked_spacecraft"] = unlockedSpacecraft,
            };
        }

        /// <summary>
        /// Computes which research IDs are actually reachable in the research tree.
        /// Mirrors the game's ResearchDefinition.GetRoot() logic:
        ///   - If ShowInTree == true, it's a root node (valid)
        ///   - Otherwise, recursively check RequirementsResearch for a valid root
        ///   - If no root ancestor found, the research is orphaned (not in tree)
        /// </summary>
        HashSet<string> ComputeValidResearch(IList allResearch, Dictionary<string, object> idToResearch)
        {
            var valid = new HashSet<string>();
            var visited = new HashSet<string>();

            foreach (var r in allResearch)
            {
                if (r == null) continue;
                var rid = GetProp<string>(r, "ID");
                if (string.IsNullOrEmpty(rid)) continue;

                visited.Clear();
                if (IsResearchInTree(r, idToResearch, visited, 0))
                    valid.Add(rid);
            }

            return valid;
        }

        bool IsResearchInTree(object rd, Dictionary<string, object> idToResearch,
            HashSet<string> visited, int depth)
        {
            // Safety: prevent infinite recursion
            if (depth > 1000) return false;

            var rid = GetProp<string>(rd, "ID");
            if (string.IsNullOrEmpty(rid)) return false;
            if (!visited.Add(rid)) return false; // cycle detected

            // Check ShowInTree property
            var showInTree = GetProp<bool>(rd, "ShowInTree");
            if (showInTree) return true;

            // Check requirementsResearch array
            var reqs = GetProp<object>(rd, "RequirementsResearch");
            if (reqs is IList reqList)
            {
                foreach (var req in reqList)
                {
                    if (req == null) continue;
                    if (IsResearchInTree(req, idToResearch, visited, depth + 1))
                        return true;
                }
            }
            else if (reqs is Array reqArray)
            {
                foreach (var req in reqArray)
                {
                    if (req == null) continue;
                    if (IsResearchInTree(req, idToResearch, visited, depth + 1))
                        return true;
                }
            }

            return false;
        }

        // ===================================================================
        // Localization
        // ===================================================================

        Dictionary<string, string> ExtractLocalization()
        {
            var loc = new Dictionary<string, string>();
            var suffixes = new[] {
                "_Description", "_Capabilities", "_Requirements", "_Warning", "_Tooltip"
            };
            var prefixes = new[] {
                "build_", "module_", "id_SpacecraftType_", "id_LV_", "spacecraft_",
                                "ID_ROCKET_", "id_rocket_", "LV_", "lv_", "BUILD_LAUNCH_",
                                "build_launch_"
            };

            var langDir = Path.Combine(Application.dataPath,
                "StreamingAssets", "Languages");
            if (!Directory.Exists(langDir)) return loc;

            var csvPath = Path.Combine(langDir, "en-US.csv");
            if (!File.Exists(csvPath)) return loc;

            foreach (var line in File.ReadAllLines(csvPath, new UTF8Encoding(false)))
            {
                var trimmed = line.Trim();
                if (string.IsNullOrEmpty(trimmed)) continue;

                var idx = trimmed.IndexOf(',');
                if (idx <= 0) continue;

                var key = trimmed.Substring(0, idx);
                var val = trimmed.Substring(idx + 1).Trim('"');

                if (prefixes.Any(p => key.StartsWith(p, StringComparison.OrdinalIgnoreCase))
                    && !suffixes.Any(s => key.EndsWith(s, StringComparison.OrdinalIgnoreCase)))
                {
                    loc[key] = val;
                }
            }

            return loc;
        }

        // ===================================================================
        // Output
        // ===================================================================

        void WriteJson(string filename, object data)
        {
            var path = Path.Combine(_dataDir, filename);
            var json = MiniJson(data);
            File.WriteAllText(path, json, new UTF8Encoding(false));
            Logger.LogInfo($"  Wrote: {filename}");
        }

        void WriteLocNames(Dictionary<string, string> loc)
        {
            var path = Path.Combine(_dataDir, "loc_names.txt");
            var lines = loc.OrderBy(kv => kv.Key)
                .Select(kv => $"{kv.Key},{kv.Value}");
            File.WriteAllLines(path, lines, new UTF8Encoding(false));
            Logger.LogInfo($"  Wrote: loc_names.txt");
        }

        void WriteMarker(string status)
        {
            var path = Path.Combine(_dataDir, "extract_plugin_ok.txt");
            File.WriteAllText(path,
                $"Plugin: {status} at {DateTime.Now:O}\n", new UTF8Encoding(false));
        }

        // ===================================================================
        // Reflection helpers
        // ===================================================================

        static T GetProp<T>(object obj, string name)
        {
            if (obj == null) return default;
            // Walk the type hierarchy to find the property
            var t = obj.GetType();
            System.Reflection.PropertyInfo p = null;
            while (t != null && p == null)
            {
                p = t.GetProperty(name,
                    BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                t = t.BaseType;
            }
            if (p == null) return default;
            try
            {
                var v = p.GetValue(obj);
                if (v is T tv) return tv;
                if (typeof(T) == typeof(double) && v is float fv) return (T)(object)(double)fv;
                if (typeof(T) == typeof(double) && v is int iv) return (T)(object)(double)iv;
                if (typeof(T) == typeof(float) && v is double dv) return (T)(object)(float)dv;
                if (typeof(T) == typeof(int))
                {
                    try { return (T)(object)System.Convert.ToInt32(v); } catch { }
                }
                return default;
            }
            catch { return default; }
        }

        static T GetField<T>(object obj, string name)
        {
            if (obj == null) return default;
            var t = obj.GetType();
            var f = t.GetField(name,
                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
            if (f == null) return default;
            try
            {
                var v = f.GetValue(obj);
                if (v is T tv) return tv;
                if (typeof(T) == typeof(int) && v is Enum ev) return (T)(object)Convert.ToInt32(ev);
                return default;
            }
            catch { return default; }
        }

        static IList GetListProp(object obj, string name)
        {
            if (obj == null) return null;
            var t = obj.GetType();
            var p = t.GetProperty(name,
                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
            if (p == null) return null;
            try { return p.GetValue(obj) as IList; }
            catch { return null; }
        }

        static Type FindTypeByName(Assembly asm, string name)
        {
            try { return asm.GetType(name); } catch { }
            try
            {
                return asm.GetTypes().FirstOrDefault(t => t.Name == name);
            }
            catch (ReflectionTypeLoadException ex)
            {
                return ex.Types?.FirstOrDefault(t => t != null && t.Name == name);
            }
        }

        // ===================================================================
        // Tiny JSON serializer (no Newtonsoft dependency)
        // ===================================================================

        static string MiniJson(object obj)
        {
            var sb = new StringBuilder();
            WriteValue(sb, obj);
            return sb.ToString();
        }

        static void WriteValue(StringBuilder sb, object obj)
        {
            if (obj == null) { sb.Append("null"); return; }
            if (obj is string s) { WriteString(sb, s); return; }
            if (obj is bool b) { sb.Append(b ? "true" : "false"); return; }
            if (obj is int i) { sb.Append(i); return; }
            if (obj is long l) { sb.Append(l); return; }
            if (obj is float f) { sb.Append(f.ToString("R", CultureInfo.InvariantCulture)); return; }
            if (obj is double d) { sb.Append(d.ToString("R", CultureInfo.InvariantCulture)); return; }
            if (obj is IDictionary dict) { WriteDict(sb, dict); return; }
            if (obj is IEnumerable enumerable && !(obj is string))
            {
                WriteArray(sb, enumerable);
                return;
            }
            WriteString(sb, obj.ToString());
        }

        static void WriteDict(StringBuilder sb, IDictionary dict)
        {
            sb.Append('{');
            var first = true;
            foreach (DictionaryEntry kv in dict)
            {
                if (!first) sb.Append(',');
                first = false;
                WriteString(sb, kv.Key.ToString());
                sb.Append(':');
                WriteValue(sb, kv.Value);
            }
            sb.Append('}');
        }

        static void WriteArray(StringBuilder sb, IEnumerable arr)
        {
            sb.Append('[');
            var first = true;
            foreach (var item in arr)
            {
                if (!first) sb.Append(',');
                first = false;
                WriteValue(sb, item);
            }
            sb.Append(']');
        }

        static void WriteString(StringBuilder sb, string s)
        {
            sb.Append('"');
            foreach (var c in s)
            {
                switch (c)
                {
                    case '"': sb.Append("\\\""); break;
                    case '\\': sb.Append("\\\\"); break;
                    case '\n': sb.Append("\\n"); break;
                    case '\r': sb.Append("\\r"); break;
                    case '\t': sb.Append("\\t"); break;
                    default: sb.Append(c); break;
                }
            }
            sb.Append('"');
        }

        // ===================================================================
        // Icon / Sprite helpers
        // ===================================================================

        /// Try to get the sprite name from an object by checking common
        /// icon/sprite properties (Sprite, Icon, icon, etc.).
        static string GetSpriteName(object obj)
        {
            if (obj == null) return null;

            // Properties that hold a UnityEngine.Sprite object
            var spritePropNames = new[] {
                "Sprite", "Icon", "icon", "sprite",
                "UISprite", "UIImage", "Image", "UiIcon",
                "RocketBackGround", "PanelImage"
            };
            foreach (var name in spritePropNames)
            {
                var sprite = GetProp<object>(obj, name);
                if (sprite != null)
                {
                    var spriteName = GetProp<string>(sprite, "name");
                    if (!string.IsNullOrEmpty(spriteName))
                        return spriteName;
                }
            }

            // String properties that directly hold a sprite name
            var stringPropNames = new[] { "SpriteId" };
            foreach (var name in stringPropNames)
            {
                var spriteName = GetProp<string>(obj, name);
                if (!string.IsNullOrEmpty(spriteName))
                    return spriteName;
            }

            return null;
        }

        // ===================================================================
        // Config
        // ===================================================================

        void DumpProperties(object obj, string label)
        {
            if (obj == null) return;
            var t = obj.GetType();
            Logger.LogInfo($"--- {label} ({t.FullName}) ---");
            foreach (var p in t.GetProperties(
                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance))
            {
                try
                {
                    var v = p.GetValue(obj);
                    var vstr = v?.ToString() ?? "null";
                    if (vstr.Length > 80) vstr = vstr.Substring(0, 77) + "...";
                    Logger.LogInfo($"  {p.Name} ({p.PropertyType.Name}) = {vstr}");
                }
                catch { Logger.LogInfo($"  {p.Name} ({p.PropertyType.Name}) = <error>"); }
            }
        }

        static string ResolveDataDir()
        {
            var dllDir = Path.GetDirectoryName(
                Assembly.GetExecutingAssembly().Location);
            var cfgPath = Path.Combine(dllDir ?? ".", "SolarExpanseExtract.cfg");

            if (File.Exists(cfgPath))
            {
                foreach (var line in File.ReadAllLines(cfgPath))
                {
                    var parts = line.Split('=', 2);
                    if (parts.Length == 2 && parts[0].Trim() == "data_dir")
                    {
                        var dir = parts[1].Trim();
                        if (dir.Length > 0) return dir;
                    }
                }
            }

            var gameRoot = Path.GetDirectoryName(Application.dataPath);
            return Path.Combine(gameRoot ?? ".", "ExtractedData");
        }
    }

    internal static class PluginInfo
    {
        public const string GUID = "SolarExpanseExtract";
        public const string Name = "Solar Expanse Data Extractor";
        public const string Version = "0.2.0";
    }
}
