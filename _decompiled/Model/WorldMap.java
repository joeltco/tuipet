/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Controller.Utility;
import Model.Battle;
import Model.Config;
import Model.Enemy;
import Model.Enum;
import Model.LootTable;
import Model.MapLevel;
import Model.Pair;
import Model.PhysicalState;
import Model.ShopConsumable;
import Model.Town;
import Model.Zone;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;

public class WorldMap {
    private final String MOD_FOLDER;
    private final String MODEL_FOLDER;
    private ArrayList<MapLevel> _maps;
    private ArrayList<Enemy> _enemies = new ArrayList();
    private PhysicalState _digimon;
    private Pair<Town, Zone> _travelTown;
    private ArrayList<Town> _towns;
    private byte _travelSpeed;
    private int _stepInc;
    private int _energyDec;
    private boolean _wildBattleWait;
    private byte _adventureLife = Config._maxAdventureLife;
    private boolean _travelRight;

    public ArrayList<MapLevel> getMaps() {
        return this._maps;
    }

    public ArrayList<Town> getTowns() {
        return this._towns;
    }

    public MapLevel[] getUnlockedMaps() {
        ArrayList<MapLevel> maps = new ArrayList<MapLevel>();
        for (int i = 1; i < this._maps.size(); ++i) {
            if (!this._maps.get(i).getIsUnlocked()) continue;
            maps.add(this._maps.get(i));
        }
        MapLevel[] m = new MapLevel[maps.size()];
        return maps.toArray(m);
    }

    public MapLevel[] getTravelMaps() {
        ArrayList<MapLevel> maps = new ArrayList<MapLevel>();
        for (int i = 1; i < this._maps.size(); ++i) {
            if (!this._maps.get(i).getIsUnlocked() || this._maps.get(i).getIsCurrent()) continue;
            maps.add(this._maps.get(i));
        }
        MapLevel[] m = new MapLevel[maps.size()];
        return maps.toArray(m);
    }

    public ArrayList<Enemy> getEnemies() {
        return this._enemies;
    }

    public Enemy getEnemy(int i) {
        Enemy enemy = null;
        for (Enemy e : this._enemies) {
            if (e.getIndex() != i) continue;
            enemy = e;
            break;
        }
        return enemy;
    }

    public void setTravelSpeed(byte newSpeed) {
        if (newSpeed > 2) {
            newSpeed = 0;
        } else if (newSpeed < 0) {
            newSpeed = 0;
        }
        this._travelSpeed = newSpeed;
    }

    public byte getTravelSpeed() {
        return this._travelSpeed;
    }

    public void setStepInc(int newStep) {
        this._stepInc = newStep;
    }

    public int getStepInc() {
        return this._stepInc;
    }

    public void setEnergyDec(int newDec) {
        if (newDec < 0) {
            newDec = 0;
        }
        this._energyDec = newDec;
    }

    public int getEnergyDec() {
        return this._energyDec;
    }

    public void setWildBattleWait(boolean newWait) {
        this._wildBattleWait = newWait;
    }

    public boolean getWildBattleWait() {
        return this._wildBattleWait;
    }

    public void setRawLife(int life) {
        this._adventureLife = (byte)life;
    }

    public byte getAdventureLife() {
        return this._adventureLife;
    }

    public void setAdventureLife(int life) {
        if (life < this._adventureLife) {
            this._digimon.setCurrentState(Enum.State.LifeDec);
        }
        if (life > Config._maxAdventureLife) {
            life = Config._maxAdventureLife;
        } else if (life <= 0) {
            life = 0;
            this.applyLifePenalty();
        }
        this._adventureLife = (byte)life;
    }

    public boolean getTravelRight() {
        return this._travelRight;
    }

    public void setTravelRight(boolean newRight) {
        this._travelRight = newRight;
    }

    public void switchTravelRight() {
        this._travelRight = !this._travelRight;
    }

    public WorldMap(PhysicalState digimon, String mod, String model) {
        this.MOD_FOLDER = mod;
        this.MODEL_FOLDER = model;
        this._digimon = digimon;
        this.initMaps();
    }

    public void startMap(int mapNum) {
        if (mapNum < this._maps.size() && mapNum > 0) {
            MapLevel oldMap = this.getCurrentMap();
            if (this.getCurrentZone() != null) {
                this.getCurrentZone().setIsCurrent(false);
            }
            if (this.getCurrentMap() != null) {
                oldMap.setIsCurrent(false);
            }
            MapLevel newMap = this.getMap(mapNum);
            newMap.setIsCurrent(true);
            newMap.setIsUnlocked(true);
            Zone zone = this.getFirstIncompleteZone();
            if (zone != null) {
                zone.setIsCurrent(true);
                zone.setIsUnlocked(true);
            }
        }
    }

    public void incSteps(Zone zone) {
        if (zone != null) {
            if (this._travelRight && zone.getCurrentLocation() - 1 < 0) {
                byte speed = this._travelSpeed;
                if (!this.toPreviousZone(zone)) {
                    this._travelSpeed = 0;
                    this.switchTravelRight();
                } else {
                    this._travelSpeed = speed;
                }
            } else {
                zone.setCurrentLocation(zone.getCurrentLocation() + (this._travelRight ? -1 : 1));
                if (zone.getCurrentLocation() >= zone.getTotalSteps()) {
                    ArrayList<Enemy> b = zone.getBosses();
                    for (Enemy e : b) {
                        if (this._travelSpeed <= 0 || !e.getIsZoneBoss() || e.getLocation()[0] != zone.getCurrentLocation() || e.isAvailable()) continue;
                        byte speed = this._travelSpeed;
                        Zone z = this.getNextZone(zone);
                        if (this.toNextZone(z, zone.getIsComplete())) {
                            this._travelSpeed = speed;
                            break;
                        }
                        this._travelSpeed = 0;
                        this.switchTravelRight();
                        break;
                    }
                }
            }
        }
    }

    public void lossPenalty(int penalty) {
        Zone zone = this.getCurrentZone();
        if (zone != null) {
            this._travelSpeed = 0;
            if (!this._travelRight) {
                penalty *= -1;
            }
            zone.setCurrentLocation(zone.getCurrentLocation() + penalty);
        }
    }

    public boolean step(Zone zone) {
        boolean isTraveling = this.checkIsTraveling();
        if (isTraveling) {
            if (!this._digimon.checkStopTravel()) {
                this._digimon.disturb();
                ++this._stepInc;
                this.checkTravelSpeed(zone);
            } else {
                this.setTravelSpeed((byte)0);
                this._digimon.setCurrentState(Enum.State.Refusing);
            }
            if (this.getCurrentZone().isTown() != null) {
                this._adventureLife = Config._maxAdventureLife;
            }
        }
        this.checkEnergyDec(isTraveling, this._digimon.isUnwell());
        return isTraveling;
    }

    private boolean checkIsTraveling() {
        boolean isTraveling = false;
        if (this._digimon.getAlive() && !this._digimon.getAsleep() && this._digimon.getAnimQueue().isEmpty() && this._digimon.getCurrentState().equals((Object)Enum.State.Idling) && this._travelSpeed > 0 && !this._wildBattleWait && this.getCurrentZone() != null && this.getCurrentMap() != null && this._digimon.getGrowthStage() != Enum.Stage.Egg) {
            isTraveling = true;
        }
        return isTraveling;
    }

    private void checkTravelSpeed(Zone zone) {
        boolean unwell = this._digimon.isUnwell();
        if (this._travelSpeed == 1 && this._stepInc >= Config._walkStepMin) {
            this._energyDec += Config._walkEnergyDec + (unwell ? Config._walkEnergyUnwellDec : (byte)0);
            this.incSteps(zone);
            this._stepInc = 0;
        } else if (this._travelSpeed == 2 && this._stepInc >= Config._runStepMin) {
            this._energyDec += Config._runEnergyDec + (unwell ? Config._runEnergyUnwellDec : (byte)0);
            this.incSteps(zone);
            this._stepInc = 0;
        }
    }

    public void isWildEncounter() {
        this._stepInc = 0;
        this._wildBattleWait = true;
    }

    public boolean battleWait(Battle b) {
        boolean escaped = false;
        if (b != null && this._wildBattleWait) {
            ++this._stepInc;
            if (this._stepInc >= Config._battleWait) {
                this._wildBattleWait = false;
                this._stepInc = 0;
                this.lossPenalty(b.getEnemy().getPenalty());
                escaped = true;
            }
        }
        return escaped;
    }

    private void checkSickInj(boolean unwell) {
        if (this._travelSpeed == 1) {
            if (unwell) {
                this._digimon.setMood(this._digimon.getMood() - Config._walkUnwellMoodDec);
            }
            this._digimon.checkWorseSick(Config._walkWorseSickChance);
            this._digimon.checkWorseTravelInj(Enum.Attribute.None, true);
        } else if (this._travelSpeed == 2) {
            this._digimon.checkWorseSick(Config._runWorseSickChance);
            this._digimon.checkWorseTravelInj(Enum.Attribute.None, false);
            if (unwell) {
                this._digimon.setMood(this._digimon.getMood() - Config._runUnwellMoodDec);
            }
        }
    }

    public int getEnergyDecPercent() {
        return (int)(100.0 * ((double)this._energyDec / (double)(Config._travelEnergyDecMaxCoefficient * this._digimon.getFullHealthPoints())));
    }

    private void checkEnergyDec(boolean isTraveling, boolean unwell) {
        if (isTraveling && this._energyDec >= Config._travelEnergyDecMaxCoefficient * this._digimon.getFullHealthPoints()) {
            this.checkSickInj(unwell);
            this._energyDec = 0;
            this._digimon.setEnergy((byte)(this._digimon.getEnergy() - Config._travelEnergyDec));
            this._digimon.setWeight(this._digimon.getWeight() - Config._travelWeightDec);
            this._digimon.setCaloriesAndChangeWeight(this._digimon.getCalories() - Config._travelCalorieDec);
            this._digimon.setEnthusiasm((byte)(this._digimon.getEnthusiasm() + Config._travelTireEnthusiasmChange));
            this._digimon.incExerciseTime();
            if (this._digimon.getExercise() < Config._travelExerciseChangeLimit) {
                this._digimon.setExercise((byte)(this._digimon.getExercise() + Config._travelExerciseInc));
            }
            if (this._digimon.getDislikedTime() == this._digimon.checkTime(this._digimon.getClock().getHours())) {
                this._digimon.setMood(this._digimon.getMood() + Config._dislikedTimeTravelMoodChange);
                this._digimon.setEnthusiasm((byte)(this._digimon.getEnthusiasm() + Config._dislikedTimeTravelEnthusiasmChange));
            }
        } else if (!isTraveling && this._energyDec > 0) {
            --this._energyDec;
        }
    }

    public Zone getCurrentZone() {
        Zone currentZone = null;
        block0: for (int i = 1; i < this._maps.size(); ++i) {
            if (!this._maps.get(i).getIsCurrent()) continue;
            for (Zone zone : this._maps.get(i).getZones()) {
                if (zone == null || !zone.getIsCurrent()) continue;
                currentZone = zone;
                break block0;
            }
            break;
        }
        return currentZone;
    }

    public MapLevel getCurrentMap() {
        MapLevel currentMap = null;
        for (int i = 1; i < this._maps.size(); ++i) {
            if (!this._maps.get(i).getIsCurrent()) continue;
            currentMap = this._maps.get(i);
            break;
        }
        return currentMap;
    }

    public MapLevel getMap(int num) {
        MapLevel m = null;
        for (int i = 1; i < this._maps.size(); ++i) {
            if (this._maps.get(i).getMapNum() != num) continue;
            m = this._maps.get(i);
            break;
        }
        return m;
    }

    public Integer[] getCurrentMapBosses() {
        int limit = 8;
        ArrayList<Integer> bosses = new ArrayList<Integer>();
        MapLevel currentMap = this.getCurrentMap();
        if (currentMap != null) {
            Enemy enemy;
            ArrayList<Zone> zones = currentMap.getZones();
            block0: for (int i = zones.size() - 1; i >= 0; --i) {
                for (int b = zones.get(i).getBosses().size() - 1; b >= 0; --b) {
                    Enemy enemy2 = zones.get(i).getBosses().get(b);
                    if (enemy2.getIsZoneBoss() && bosses.size() < limit) {
                        bosses.add(enemy2.getIndex());
                        continue;
                    }
                    if (bosses.size() >= limit) break block0;
                }
            }
            if (bosses.size() < limit) {
                block2: for (Zone zone : zones) {
                    for (int b = zone.getBosses().size() - 1; b >= 0; --b) {
                        enemy = zone.getBosses().get(b);
                        if (enemy.getIsZoneBoss()) continue;
                        bosses.add(enemy.getIndex());
                        if (bosses.size() >= limit) break block2;
                    }
                }
            }
            block4: while (bosses.size() < limit) {
                for (Zone zone : zones) {
                    for (int b = zone.getRandoms().size() - 1; b >= 0; --b) {
                        enemy = zone.getBosses().get(b);
                        bosses.add(enemy.getIndex());
                        if (bosses.size() >= limit) continue block4;
                    }
                }
            }
        }
        Integer[] b = new Integer[bosses.size()];
        b = bosses.toArray(b);
        return b;
    }

    public boolean changeMap(int id) {
        MapLevel map = this.getMap(id);
        Zone newZone = map.getZones().get(0);
        for (Zone z : map.getZones()) {
            if (!z.getIsCurrent()) continue;
            newZone = z;
            break;
        }
        return this.changeZone(this.getCurrentZone().getIsComplete(), newZone);
    }

    public boolean changeZone(boolean isComplete, Zone newZone) {
        return this.changeZone(isComplete, newZone, true);
    }

    public boolean changeZone(boolean isComplete, Zone newZone, boolean changeHabitat) {
        this._travelSpeed = 0;
        Zone currentZone = this.getCurrentZone();
        if (currentZone != null && newZone != null && currentZone != newZone) {
            currentZone.setIsComplete(isComplete);
            MapLevel currentMap = this.getCurrentMap();
            boolean isLastZone = this.currentIsLastZone();
            if (isLastZone && currentZone.getIsComplete()) {
                currentMap.setIsComplete(true);
            }
            if (newZone.getMapNum() != currentMap.getMapNum()) {
                MapLevel map = this.getCurrentMap();
                map.setIsCurrent(false);
                MapLevel newMap = this.getMap(newZone.getMapNum());
                newMap.setIsCurrent(true);
            }
            currentZone.leaveZone();
            newZone.enterZone();
            if (newZone != currentZone) {
                newZone.setCurrentLocation(0);
            } else if (isLastZone) {
                currentZone.setCurrentLocation(currentZone.getTowns().get(0).getBackgroundRange().getRange()[0]);
            }
            if (changeHabitat) {
                this._digimon.setCurrentHabitat(newZone.getCurrentLocationBackground());
            }
            return true;
        }
        return false;
    }

    private Zone getFirstIncompleteZone() {
        Zone incompleteZone = null;
        for (Zone zone : this.getCurrentMap().getZones()) {
            if (zone == null || zone.getIsComplete()) continue;
            incompleteZone = zone;
            break;
        }
        return incompleteZone;
    }

    private boolean currentIsLastZone() {
        boolean isLastZone = false;
        Zone current = this.getCurrentZone();
        ArrayList<Zone> zones = this.getCurrentMap().getZones();
        if (zones.get(zones.size() - 1).getZoneNum() == current.getZoneNum()) {
            isLastZone = true;
        }
        return isLastZone;
    }

    public MapLevel getFirstIncompleteMap() {
        MapLevel incompleteMap = null;
        for (int i = 1; i < this._maps.size(); ++i) {
            if (this._maps.get(i).getIsComplete()) continue;
            incompleteMap = this._maps.get(i);
            break;
        }
        return incompleteMap;
    }

    private void writeMaps() {
        try (PrintWriter save = new PrintWriter("maps.csv");){
            save.println("Zones,MapNum");
            for (MapLevel map : this._maps) {
                save.println(map.infoToString());
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void writeZones() {
        try (PrintWriter save = new PrintWriter("zones.csv");){
            save.println("MapNum,ZoneNum,Bosses,Randoms,LocX,LocY,TotalSteps");
            for (int i = 1; i < this._maps.size(); ++i) {
                for (Zone zone : this._maps.get(i).getZones()) {
                    save.println(zone.infoToString(this._maps.get(i).getMapNum()));
                }
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    /*
     * Enabled aggressive exception aggregation
     */
    private ArrayList<ShopConsumable> readShopConsumables() {
        try (InputStream in = Utility.getInputStream(this.MOD_FOLDER, this.MODEL_FOLDER, "shopConsumable.csv");){
            ArrayList<ShopConsumable> arrayList;
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(in));){
                ArrayList<ShopConsumable> list = new ArrayList<ShopConsumable>();
                String line = reader.readLine();
                while ((line = reader.readLine()) != null) {
                    ShopConsumable c = new ShopConsumable(line.split(","));
                    list.add(c);
                }
                arrayList = list;
            }
            return arrayList;
        }
        catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }

    private void readMaps() {
        try (InputStream in = Utility.getInputStream(this.MOD_FOLDER, this.MODEL_FOLDER, "maps.csv");
             BufferedReader reader = new BufferedReader(new InputStreamReader(in));){
            String line = reader.readLine();
            while ((line = reader.readLine()) != null) {
                MapLevel map = new MapLevel();
                this._maps.add(map.readInfoString(line));
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    private ArrayList<Town> readTowns(ArrayList<ShopConsumable> consumables) {
        ArrayList<Town> towns = new ArrayList<Town>();
        try (InputStream in = Utility.getInputStream(this.MOD_FOLDER, this.MODEL_FOLDER, "towns.csv");
             BufferedReader reader = new BufferedReader(new InputStreamReader(in));){
            String line = reader.readLine();
            while ((line = reader.readLine()) != null) {
                towns.add(new Town(line.split(","), consumables));
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
        return towns;
    }

    private void readZones(ArrayList<ShopConsumable> consumables) {
        this._towns = this.readTowns(consumables);
        try (InputStream in = Utility.getInputStream(this.MOD_FOLDER, this.MODEL_FOLDER, "zones.csv");
             BufferedReader reader = new BufferedReader(new InputStreamReader(in));){
            String line = reader.readLine();
            block12: while ((line = reader.readLine()) != null) {
                Zone zone = new Zone(this._digimon);
                zone.readInfoString(line, this._towns);
                for (int i = 1; i < this._maps.size(); ++i) {
                    if (this._maps.get(i).getMapNum() != zone.getMapNum()) continue;
                    this._maps.get(i).addZone(zone);
                    continue block12;
                }
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void writeEnemies() {
        try (PrintWriter save = new PrintWriter("enemies.csv");){
            save.println("Name,Map,Zone,Health,VaccinePower,DataPower,VirusPower,Penalty,IsRandom,Location");
            for (int i = 1; i < this._maps.size(); ++i) {
                for (Zone zone : this._maps.get(i).getZones()) {
                    for (Enemy enemy : zone.getBosses()) {
                        save.println(enemy.infoToString());
                    }
                    for (Enemy enemy : zone.getRandoms()) {
                        save.println(enemy.infoToString());
                    }
                }
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void readEnemies() {
        try (InputStream in = Utility.getInputStream(this.MOD_FOLDER, this.MODEL_FOLDER, "enemies.csv");
             BufferedReader reader = new BufferedReader(new InputStreamReader(in));){
            LootTable loot = new LootTable(this.MOD_FOLDER, this.MODEL_FOLDER);
            String line = reader.readLine();
            while ((line = reader.readLine()) != null) {
                Enemy enemy = new Enemy();
                enemy.readInfoString(line, this._digimon, loot);
                this._enemies.add(enemy);
                block13: for (int i = 1; i < this._maps.size(); ++i) {
                    if (this._maps.get(i).getMapNum() != enemy.getMap()) continue;
                    for (Zone zone : this._maps.get(i).getZones()) {
                        if (zone.getZoneNum() != enemy.getZone()) continue;
                        if (enemy.getIsRandom()) {
                            zone.addRandom(enemy);
                            continue block13;
                        }
                        zone.addBoss(enemy);
                        continue block13;
                    }
                }
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    public void initMaps() {
        this._maps = new ArrayList();
        ArrayList<ShopConsumable> c = this.readShopConsumables();
        this.readMaps();
        this.readZones(c);
        this.readEnemies();
    }

    public void applyLifePenalty() {
        if (!this.toClosestTown()) {
            this.getCurrentZone().setCurrentLocation(0);
        }
        this._digimon.setCurrentState(Enum.State.Retreat_Town);
    }

    public Enemy getNextBoss() {
        Zone zone = this.getCurrentZone();
        int travelDistance = 0;
        int max = 0;
        for (Zone z : this.getCurrentMap().getZones()) {
            max += z.getTotalSteps();
        }
        Enemy enemy = zone.getClosestNextBoss(this._travelRight, zone.getCurrentLocation());
        while (enemy == null && travelDistance < max) {
            travelDistance += zone.getTotalSteps();
            zone = this._travelRight ? this.getPreviousZone(zone) : this.getNextZone(zone);
            if (!zone.getIsUnlocked() || (enemy = zone.getClosestNextBoss(this._travelRight, this._travelRight ? zone.getTotalSteps() : 0)) == null) continue;
            if (!this._travelRight) {
                travelDistance += enemy.getLocation()[0];
                continue;
            }
            travelDistance += zone.getTotalSteps() - enemy.getLocation()[1];
        }
        return enemy;
    }

    private Pair<Town, Zone> getClosestTownZone() {
        Town leftTown;
        Zone zone = this.getCurrentZone();
        int location = zone.getCurrentLocation();
        int left = 0;
        int right = 0;
        int max = 0;
        for (Zone z : this.getCurrentMap().getZones()) {
            max += z.getTotalSteps();
        }
        Town rightTown = leftTown = zone.getClosestTown(location);
        Town town = leftTown;
        Zone leftZone = zone;
        if (leftTown != null && leftTown.getStartingLocation() < location) {
            leftTown = null;
        }
        left = leftTown == null ? (left += Math.abs(location - zone.getTotalSteps())) : (left += leftTown.getStartingLocation() - location);
        while (leftTown == null && left < max) {
            if ((leftZone = this.getNextZone(leftZone)).getIsUnlocked() && !leftZone.getTowns().isEmpty()) {
                ArrayList<Town> towns = new ArrayList<Town>(leftZone.getTowns());
                Collections.sort(towns, Comparator.comparing(Town::getStartingLocation, Comparator.naturalOrder()));
                leftTown = towns.get(0);
                if (leftTown.isUnlocked()) {
                    left += leftTown.getStartingLocation();
                    continue;
                }
                leftTown = null;
                left += leftZone.getTotalSteps();
                continue;
            }
            left += leftZone.getTotalSteps();
        }
        Zone rightZone = zone;
        if (rightTown != null && rightTown.getEndingLocation() > location) {
            rightTown = null;
        }
        right = rightTown == null ? (right += location) : (right += location - rightTown.getEndingLocation());
        while (rightTown == null && right < max) {
            if ((rightZone = this.getPreviousZone(rightZone)).getIsUnlocked() && !rightZone.getTowns().isEmpty()) {
                ArrayList<Town> towns = new ArrayList<Town>(rightZone.getTowns());
                Collections.sort(towns, Comparator.comparing(Town::getStartingLocation, Comparator.naturalOrder()));
                rightTown = towns.getLast();
                if (rightTown.isUnlocked()) {
                    right += rightZone.getTotalSteps() - rightTown.getEndingLocation();
                    continue;
                }
                rightTown = null;
                right += rightZone.getTotalSteps();
                continue;
            }
            right += rightZone.getTotalSteps();
        }
        if (left < right) {
            town = leftTown;
            zone = leftZone;
        } else if (left > right) {
            town = rightTown;
            zone = rightZone;
        }
        if (town != null) {
            return new Pair<Town, Zone>(town, zone);
        }
        return null;
    }

    public boolean isTownClose() {
        this._travelTown = this.getClosestTownZone();
        return this._travelTown != null;
    }

    public boolean toClosestTown() {
        this._travelTown = this.getClosestTownZone();
        return this.toTravelTown();
    }

    public boolean toTravelTown() {
        if (this._travelTown != null && this._travelTown._a != null && this._travelTown._b != null) {
            this.changeZone(this.getCurrentZone().getIsComplete(), (Zone)this._travelTown._b);
            if (this._travelRight) {
                ((Zone)this._travelTown._b).setCurrentLocation(((Town)this._travelTown._a).getEndingLocation());
            } else {
                ((Zone)this._travelTown._b).setCurrentLocation(((Town)this._travelTown._a).getStartingLocation());
            }
            this._digimon.setCurrentHabitat(this.getCurrentZone().getCurrentLocationBackground());
            return true;
        }
        return false;
    }

    private MapLevel getNextMap(MapLevel m) {
        return this.getCurrentMap();
    }

    private MapLevel getPreviousMap(MapLevel m) {
        return this.getCurrentMap();
    }

    private Zone getNextZone(Zone z) {
        MapLevel map = this.getMap(z.getMapNum());
        ArrayList<Zone> zones = map.getZones();
        int index = zones.indexOf(z);
        if (index > -1) {
            if (index + 1 < zones.size()) {
                return zones.get(index + 1);
            }
            return this.getNextMap(map).getZones().get(0);
        }
        return null;
    }

    public boolean completeZone() {
        Zone current = this.getCurrentZone();
        Zone z = this.getNextZone(current);
        z.setIsUnlocked(true);
        return this.toNextZone(z, true);
    }

    private boolean toNextZone(Zone next, boolean complete) {
        if (next != null && next.getIsUnlocked()) {
            this.changeZone(complete, next);
            return true;
        }
        return false;
    }

    private Zone getPreviousZone(Zone z) {
        MapLevel map = this.getMap(z.getMapNum());
        ArrayList<Zone> zones = map.getZones();
        int index = zones.indexOf(z);
        if (index > -1) {
            if (index - 1 < 0) {
                return this.getPreviousMap(map).getZones().getLast();
            }
            return zones.get(index - 1);
        }
        return null;
    }

    private boolean toPreviousZone(Zone current) {
        Zone z = this.getPreviousZone(current);
        if (z != null && z.getIsUnlocked()) {
            this.changeZone(current.getIsComplete(), z);
            z.setCurrentLocation(z.getTotalSteps() - 1);
            return true;
        }
        return false;
    }
}

