/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Controller.Utility;
import Model.BackgroundRange;
import Model.Config;
import Model.Consumable;
import Model.Enemy;
import Model.Enum;
import Model.FoodType;
import Model.Item;
import Model.PhysicalState;
import Model.Town;
import java.util.ArrayList;
import java.util.Random;

public class Zone {
    private PhysicalState _digimon;
    private byte _zoneNum;
    private int _mapNum;
    private ArrayList<Enemy> _bosses = new ArrayList();
    private ArrayList<Enemy> _randoms = new ArrayList();
    private int _locX;
    private int _locY;
    private int _currentLocation;
    private int _totalSteps;
    private boolean _isComplete;
    private boolean _isCurrent;
    private boolean _isUnlocked;
    private ArrayList<BackgroundRange> _backgrounds = new ArrayList();
    private ArrayList<Town> _towns = new ArrayList();
    private ArrayList<Item> _items = new ArrayList();
    private ArrayList<FoodType> _foods = new ArrayList();

    public byte getZoneNum() {
        return this._zoneNum;
    }

    public int getMapNum() {
        return this._mapNum;
    }

    public ArrayList<Enemy> getBosses() {
        return this._bosses;
    }

    public ArrayList<Enemy> getRandoms() {
        return this._randoms;
    }

    public int[] getLoc() {
        return new int[]{this._locX, this._locY};
    }

    public void setLoc(int x, int y) {
        this._locX = x;
        this._locY = y;
    }

    public void setCurrentLocation(int newLocation) {
        if (newLocation < 0) {
            newLocation = 0;
        }
        if (newLocation > this._totalSteps) {
            newLocation = this._totalSteps;
        }
        this._currentLocation = newLocation;
    }

    public int getCurrentLocation() {
        return this._currentLocation;
    }

    public void setTotalSteps(int newSteps) {
        this._totalSteps = newSteps;
    }

    public int getTotalSteps() {
        return this._totalSteps;
    }

    public void setIsComplete(boolean newComplete) {
        this._isComplete = newComplete;
    }

    public boolean getIsComplete() {
        return this._isComplete;
    }

    public void setIsCurrent(boolean newCurrent) {
        this._isCurrent = newCurrent;
    }

    public boolean getIsCurrent() {
        return this._isCurrent;
    }

    public void setIsUnlocked(boolean newUnlocked) {
        this._isUnlocked = newUnlocked;
    }

    public boolean getIsUnlocked() {
        return this._isUnlocked;
    }

    public ArrayList<BackgroundRange> getBackgrounds() {
        return this._backgrounds;
    }

    public ArrayList<Town> getTowns() {
        return this._towns;
    }

    public void enterZone() {
        this._isUnlocked = true;
        this._isCurrent = true;
    }

    public void leaveZone() {
        this._isUnlocked = true;
        this._isCurrent = false;
    }

    public Enemy getClosestNextBoss(boolean isRight, int loc) {
        Enemy enemy = null;
        int difference = Integer.MAX_VALUE;
        for (Enemy e : this._bosses) {
            int check;
            if (!e.isAvailable() || !(isRight ? loc >= e.getLocation()[1] : loc <= e.getLocation()[0]) || Math.abs(loc - (check = e.getLocation()[isRight ? 1 : 0])) >= difference) continue;
            difference = Math.abs(loc - check);
            enemy = e;
        }
        return enemy;
    }

    public Town getClosestTown(int location) {
        Town town = null;
        int distance = Integer.MAX_VALUE;
        if (!this._towns.isEmpty()) {
            for (Town t : this._towns) {
                int median;
                int d;
                if (!t.isUnlocked() || (d = Math.abs(location - (median = (t.getBackgroundRange().getRange()[0] + t.getBackgroundRange().getRange()[1]) / 2))) >= distance || location >= t.getBackgroundRange().getRange()[0] && location <= t.getBackgroundRange().getRange()[1]) continue;
                distance = d;
                town = t;
            }
        }
        return town;
    }

    public ArrayList<Item> getItems() {
        return this._items;
    }

    public ArrayList<FoodType> getFoods() {
        return this._foods;
    }

    public Zone(PhysicalState digimon) {
        this._digimon = digimon;
    }

    public Zone(int zoneNum, int totalSteps) {
        this._zoneNum = (byte)zoneNum;
        this._isComplete = false;
        this._currentLocation = 0;
        this._totalSteps = totalSteps;
    }

    public Zone readInfoString(String zone, ArrayList<Town> towns) {
        try {
            String[] backgrounds;
            String[] info = zone.split(",");
            this._mapNum = Integer.parseInt(info[0]);
            this._zoneNum = (byte)Integer.parseInt(info[1]);
            this._locX = Integer.parseInt(info[2]);
            this._locY = Integer.parseInt(info[3]);
            this._totalSteps = Integer.parseInt(info[4]);
            for (String s : backgrounds = info[5].split(";")) {
                this._backgrounds.add(new BackgroundRange(s));
            }
            try {
                this.addTown(info[6].split(";"), towns);
            }
            catch (Exception ex) {
                ex.printStackTrace();
            }
            try {
                String[] items;
                for (String s : items = info[7].split(":")) {
                    this._items.add(this._digimon.getItems().get(Integer.parseInt(s)));
                }
            }
            catch (Exception ex) {
                ex.printStackTrace();
            }
            try {
                String[] foods;
                for (String s : foods = info[8].split(":")) {
                    this._foods.add(this._digimon.getFoodTypes().get(Integer.parseInt(s)));
                }
            }
            catch (Exception ex) {
                ex.printStackTrace();
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
        return this;
    }

    public String infoToString(int mapNum) {
        StringBuilder info = new StringBuilder();
        String delin = ",";
        info.append(mapNum);
        info.append(delin);
        info.append(this._zoneNum);
        info.append(delin);
        info.append(this._locX);
        info.append(delin);
        info.append(this._locY);
        info.append(delin);
        info.append(this._totalSteps);
        return info.toString();
    }

    public void addTown(String[] data, ArrayList<Town> towns) {
        if (!towns.isEmpty() && data.length > 0) {
            for (String s : data) {
                int id;
                if (s.isEmpty() || (id = Integer.parseInt(s)) <= -1 || id >= towns.size()) continue;
                this._towns.add(towns.get(id));
            }
        }
    }

    public void addBoss(Enemy boss) {
        try {
            if (!this._bosses.contains(boss)) {
                this._bosses.add(boss);
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    public void addRandom(Enemy random) {
        try {
            if (!this._randoms.contains(random)) {
                this._randoms.add(random);
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    public Town isTown() {
        if (this._towns != null) {
            for (Town town : this._towns) {
                BackgroundRange r = town.getBackgroundRange();
                if (this._currentLocation < r.getRange()[0] || this._currentLocation > r.getRange()[1]) continue;
                town.setUnlocked(true);
                return town;
            }
        }
        return null;
    }

    public int getCurrentLocationBackground() {
        int id = -1;
        Town town = this.isTown();
        id = town != null ? town.getBackgroundRange().getBackgroundID() : this.getCurrentLocationBackgroundRange().getBackgroundID();
        return id;
    }

    public BackgroundRange getCurrentLocationBackgroundRange() {
        BackgroundRange id = null;
        for (BackgroundRange r : this._backgrounds) {
            if (this._currentLocation < r.getRange()[0] || this._currentLocation > r.getRange()[1]) continue;
            id = r;
            break;
        }
        return id;
    }

    public boolean checkInvestigate() {
        int moodFactor;
        byte travelSpeed;
        boolean investigate = false;
        Random r = new Random();
        boolean isNight = this._digimon.checkTime(this._digimon.getClock().getHours()).equals((Object)Enum.Time.Night);
        int seed = Config._investigateChance + (isNight ? Config._investigateNightFactor : 0) + ((travelSpeed = this._digimon.getWorld().getTravelSpeed()) == 1 ? Config._investigateWalkFactor : 0) + (moodFactor = -(this._digimon.getObedience() + this._digimon.getMood()));
        int prob = r.nextInt(seed <= 0 ? 1 : seed);
        if (prob == 0) {
            investigate = true;
        }
        return investigate;
    }

    public int[] checkItem() {
        int prob;
        int[] c = null;
        Consumable i = null;
        Consumable f = null;
        Random r = new Random();
        int totalItems = this._foods.size() + this._items.size();
        if (totalItems > 0) {
            int giftNum = r.nextInt(totalItems);
            if (giftNum >= this._foods.size()) {
                i = this._items.get(giftNum -= this._foods.size());
            } else {
                f = this._foods.get(giftNum);
            }
        }
        if (i != null) {
            if (i.canIncQuantity()) {
                c = new int[]{i.getID(), 0};
            }
        } else if (f != null && f.canIncQuantity()) {
            c = new int[]{f.getID(), 1};
        }
        if ((prob = r.nextInt(Config._investigateEnemyChance == 0 ? 1 : Config._investigateEnemyChance)) == 0) {
            c = null;
        }
        return c;
    }

    public Enemy checkBattle(boolean investigate) {
        Enemy enemy = null;
        byte travelSpeed = this._digimon.getWorld().getTravelSpeed();
        if (this.isTown() == null || investigate) {
            if (travelSpeed > 0) {
                for (Enemy boss : this._bosses) {
                    if (boss.getLocation()[0] != this._currentLocation || !this.checkTime(boss.getTime())) continue;
                    enemy = boss;
                    break;
                }
            }
            if (enemy == null && (!this._digimon.getBattleImmunity() || investigate) && this._currentLocation < this._totalSteps && this._digimon.getCurrentState().equals((Object)Enum.State.Idling)) {
                int encounterChance;
                boolean isNight = this._digimon.checkTime(this._digimon.getClock().getHours()).equals((Object)Enum.Time.Night);
                Random ran = new Random();
                double prob = Config._randomChance - (isNight ? Config._randomChance / Config._randomEncounterNightCoefficient : 0.0) + (travelSpeed > 1 ? Config._randomChance / Config._randomEncounterRunCoefficient : (travelSpeed > 0 ? Config._randomChance / Config._randomEncounterWalkCoefficient : Config._randomChance / Config._randomEncounterStillCoefficient));
                if (prob <= 0.0) {
                    prob = 1.0;
                }
                if ((encounterChance = ran.nextInt((int)(prob = Math.ceil(prob)))) == 0) {
                    ArrayList<Enemy> encounters = new ArrayList<Enemy>();
                    while (encounters.size() == 0) {
                        for (Enemy encounter : this._randoms) {
                            if (encounter.getLocation()[0] > this._currentLocation || encounter.getLocation()[1] < this._currentLocation || !this.checkTime(encounter.getTime()) || !Utility.randomChance(encounter.getRandomChance(), 100)) continue;
                            encounters.add(encounter);
                        }
                    }
                    int randomEnemy = ran.nextInt(encounters.size());
                    enemy = (Enemy)encounters.get(randomEnemy);
                }
            }
            if (enemy != null && !enemy.isAvailable()) {
                enemy = null;
            }
        }
        return enemy;
    }

    public boolean checkTime(Enum.Time t) {
        return t.equals((Object)Enum.Time.None) || this._digimon.checkTime(this._digimon.getClock().getHours()).equals((Object)t);
    }
}

