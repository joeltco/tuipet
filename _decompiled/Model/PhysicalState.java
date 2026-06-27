/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Controller.Checksum;
import Controller.Utility;
import Model.Affinity;
import Model.BackgroundRange;
import Model.Battle;
import Model.CareEffect;
import Model.Config;
import Model.Consumable;
import Model.CrashEntry;
import Model.Cryption;
import Model.CurrentTime;
import Model.DNA;
import Model.Enemy;
import Model.Enum;
import Model.Evolution;
import Model.EvolutionInfo;
import Model.FoodType;
import Model.Habitat;
import Model.Item;
import Model.MapLevel;
import Model.MinLapsePacket;
import Model.ShopConsumable;
import Model.Taste;
import Model.Tournament;
import Model.Town;
import Model.Trophy;
import Model.ViewSettings;
import Model.WeatherRecord;
import Model.WorldMap;
import Model.Zone;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Calendar;
import java.util.Collections;
import java.util.Comparator;
import java.util.Iterator;
import java.util.Random;
import javax.swing.JTextArea;

public class PhysicalState {
    private final String MOD_FOLDER;
    private final String MODEL_FOLDER;
    private long _saveTime;
    private boolean _timeSkip;
    private String _checksum;
    private boolean _gameModified;
    private final boolean _tournamentVersion;
    private boolean _saving;
    private boolean _paused;
    private int _difficultySetting;
    private final String _cryptKey = "hackero/";
    private ArrayList<Integer> _dailyTrophies = new ArrayList();
    private ArrayList<Integer> _foughtTrophiesToday = new ArrayList();
    private int[] _trophySchedule;
    private Tournament _tournament;
    private Affinity _affinity;
    private ArrayList<FoodType> _foodTypes;
    private ArrayList<Item> _items;
    private DNA _dna = new DNA();
    private byte _savedFromDeath;
    private byte _hungerDecayLapse;
    private byte _strengthDecayLapse;
    private int _minToDecayHunger = 59;
    private int _minToDecayStrength = 59;
    private double _hungerDecayCoefficient;
    private double _strengthDecayCoefficient;
    private int _xAntibodyCount;
    private Enum.XAntibodyState _xAntibodyState = Enum.XAntibodyState.None;
    private CurrentTime _clock;
    private Enum.Weather _currentWeather = Enum.Weather.Clear;
    private byte _temp;
    private byte _dayTemp;
    private byte _tempGoal = (byte)101;
    private byte[] _idealTemp = new byte[2];
    private int[] _tempRecord = new int[2];
    private int[] _obedienceRecord = new int[2];
    private int _day;
    private String _saveString;
    private boolean _loading;
    private final Evolution _evolution;
    private int _spriteNum;
    private int _spriteSet;
    private Enum.State _currentState = Enum.State.Idling;
    private ArrayList<Enum.State> _animQueue = new ArrayList();
    private int _index;
    private int _age;
    private int _bonus;
    private int _timeToAge;
    private int _callMinutesPoop;
    private int _callMinutesHunger;
    private int _callMinutesStrength;
    private int _callMinutesLights;
    private int _callMinutesDiscipline;
    private Taste<Enum.Food> _foodRanks;
    private Taste<Enum.Time> _timeRanks;
    private Taste<Enum.Attribute> _attributeRanks;
    private int _energyRank;
    private int _weightRank;
    private int _moodRank;
    private byte _praiseWindow;
    private boolean _praise;
    private byte _scoldWindow;
    private boolean _scold;
    private boolean _refused;
    private boolean _compliance;
    private boolean _useWeakConsumable;
    private int _mood;
    private Enum.Mood _currentMood;
    private byte _enthusiasm;
    private int _obedience;
    private byte _obedienceChangeLapse;
    private byte _itemInterest;
    private byte _itemInterestLapse = Config._itemInterestTimer;
    private byte _surrender;
    private byte _glutton;
    private byte _restless;
    private byte _disposition;
    private Enum.Personality _personality;
    private byte _hunger;
    private byte _stomachCapacity;
    private byte _maxEnergy;
    private byte _exerciseLimit;
    private byte _exercise;
    private byte _energy;
    private byte _energyGain;
    private byte _napEnergyGain;
    private int _sleepMinutesToEnergyGain;
    private int _sleepMinutes;
    private int _weight;
    private int _baseWeight;
    private int _calories;
    private int _calorieMinMod;
    private int _calorieMaxMod;
    private byte _fullHealthPoints;
    private byte _healthPoints = (byte)5;
    private Enum.Attribute _attribute;
    private Enum.Field _field = Enum.Field.None;
    private Enum.Element _element = Enum.Element.None;
    private int _vaccinePower;
    private int _dataPower;
    private int _virusPower;
    private int _morningTrain;
    private int _dayTrain;
    private int _nightTrain;
    private int _battles;
    private int _wins;
    private int _perfectWins;
    private int _bits;
    private long _totalLifespan;
    private long _lapsedLife;
    private Enum.Stage _growthStage = Enum.Stage.None;
    private long _growthPeriod;
    private boolean _alive;
    private Enum.Weight _overweight;
    private int _disturb;
    private int _overeat;
    private int _mistake;
    private int _mistakeDay;
    private boolean _lightsOffMistake;
    private byte[] _filth = new byte[6];
    private int _bmGauge;
    private byte _bmLapseInc;
    private byte _bmMax;
    private double _poopSickBoundMultiplier;
    private int _filthLapseMoodChange;
    private boolean _asleep;
    private boolean _lights;
    private boolean _autoCare;
    private int _assistantID;
    private int _tourneyAlarm = -1;
    private int _sickCount;
    private int _injCount;
    private byte _vitaminLapse;
    private byte _bandageLapse;
    private boolean _nap;
    private byte _toNapSleepLapse;
    private byte _napEnergyInc;
    private int _napCycle;
    private byte _medLapse;
    private byte _injLength;
    private byte _sickLength;
    private byte _fatigueLength;
    private int _sleepLapse;
    private int _sleepLimit;
    private int _awakeLapse;
    private int _awakeLimit;
    private int _sleepLapseInc;
    private int _awakeLapseInc;
    private boolean _disciplineCall;
    private WorldMap _world;
    private ArrayList<int[]> _evolHistory = new ArrayList();
    private ArrayList<ArrayList<int[]>> _generationHistory = new ArrayList();
    private int _currentHabitat;
    private int _homeHabitat;
    private ArrayList<Habitat> _habitats;
    private ArrayList<CareEffect> _careEffects;
    private boolean _isHome = true;
    private int _battleImmunity;
    private boolean _isFree;
    private boolean _isFavorite;
    private ArrayList<ShopConsumable> _homeItemShop = new ArrayList();
    private ArrayList<ShopConsumable> _homeFoodShop = new ArrayList();
    private int _meatEaten;
    private int _vegEaten;
    private int _fruitEaten;
    private int _fishEaten;
    private int _junkEaten;
    private int _medEaten;
    private int _grainEaten;
    private int _dairyEaten;
    private ArrayList<Integer> _levelsFought = new ArrayList();
    private ViewSettings _settings;
    private int[] _moodRecord = new int[Enum.Mood.values().length];
    private int[] _dailyMoodRecord = new int[Enum.Mood.values().length];
    private int[] _habitatRecord;
    private int[] _weightRecord = new int[Enum.Weight.values().length];
    private int[] _gift = new int[2];
    private String _requestMessage;
    private final String _napRequest = "Your Digimon is tired and wants to nap";
    private final String _purchaseRequest = "Your Digimon wants to buy the";
    private final String _foodRequest = "Your Digimon wants to eat the";
    private final String _itemRequest = "Your Digimon wants to use the";
    private final String _battleRequest = "Your Digimon wants to fight in a tournament";
    private final String _homeRequest = "Your Digimon wants to go home";
    private final String _adventureRequest = "Your Digimon wants to go to the Digital World";
    private final String _warmRequest = "Your Digimon wants to cool down";
    private final String _coldRequest = "Your Digimon wants to warm up";
    private final String _attentionRequest = "Your Digimon wants a hug";
    private ArrayList<WeatherRecord> _weatherRecord = new ArrayList();
    private boolean _canEvolveOrDie = true;
    private boolean _postponeEvolve = false;
    private boolean _postponeDie = false;
    private byte _protein;
    private byte _mineral;
    private byte _vitamin;
    private byte _restock;
    private byte _toiletTrained;
    private int _unlockConsumable = -1;

    public void setGameModified(boolean b) {
        if (!this._gameModified) {
            this._gameModified = b;
        }
    }

    public boolean isPaused() {
        return this._paused;
    }

    public void setPaused(boolean p) {
        this._paused = p;
    }

    public String getChecksum() {
        return this._checksum;
    }

    public void setChecksum(String c) {
        this._checksum = c;
    }

    public boolean getTimeSkip() {
        return this._timeSkip;
    }

    public void setTimeSkip(boolean b) {
        this._timeSkip = b;
    }

    public boolean getGameModified() {
        return this._gameModified;
    }

    public boolean getIsTournamentVersion() {
        return this._tournamentVersion;
    }

    public boolean getIsFavorite() {
        return this._isFavorite;
    }

    public void setIsFavorite(boolean b) {
        this._isFavorite = b;
    }

    public boolean getIsFree() {
        return this._isFree;
    }

    public void setIsFree(boolean f) {
        this._isFree = f;
    }

    public byte getSavedFromDeath() {
        return this._savedFromDeath;
    }

    public void setSavedFromDeath(int i) {
        this._savedFromDeath = (byte)i;
    }

    public Item getDigimemory() {
        return this._items.get(32);
    }

    public void setHomeItemShop(ArrayList<ShopConsumable> items) {
        this._homeItemShop = items;
    }

    public ArrayList<ShopConsumable> getHomeItemShop() {
        if (!this._isHome) {
            Town t = this._world.getCurrentZone().isTown();
            if (t != null) {
                ArrayList<ShopConsumable> shop = t.getItemShop();
                if (shop.isEmpty()) {
                    return t.getItemShop(this);
                }
                return shop;
            }
            return new ArrayList<ShopConsumable>();
        }
        if (this._homeItemShop.isEmpty()) {
            ArrayList<Consumable> iList = new ArrayList<Consumable>();
            iList.addAll(this._items);
            this._homeItemShop = this.randomizeShop(null, iList, Config._maxItemShopInventory, false, true, true);
            return this._homeItemShop;
        }
        return this._homeItemShop;
    }

    public void setHomeFoodShop(ArrayList<ShopConsumable> foods) {
        this._homeFoodShop = foods;
    }

    public ArrayList<ShopConsumable> getHomeFoodShop() {
        if (!this._isHome) {
            Town t = this._world.getCurrentZone().isTown();
            if (t != null) {
                ArrayList<ShopConsumable> shop = t.getFoodShop();
                if (shop.isEmpty()) {
                    return t.getFoodShop(this);
                }
                return shop;
            }
            return new ArrayList<ShopConsumable>();
        }
        if (this._homeFoodShop.isEmpty()) {
            ArrayList<Consumable> fList = new ArrayList<Consumable>();
            fList.addAll(this._foodTypes);
            this._homeFoodShop = this.randomizeShop(null, fList, Config._maxFoodShopInventory, true, true, true);
            return this._homeFoodShop;
        }
        return this._homeFoodShop;
    }

    public boolean getCanSell(boolean isFood) {
        if (this._isHome) {
            return isFood ? Config._canSellFood : Config._canSellItems;
        }
        Town t = this._world.getCurrentZone().isTown();
        if (t != null) {
            return isFood ? t.getCanSellFood() : t.getCanSellItems();
        }
        return false;
    }

    public void setXAntibodyState(Enum.XAntibodyState s) {
        switch (this._xAntibodyState) {
            case None: 
            case Temporary: {
                this._xAntibodyState = s;
                break;
            }
            case XProgram: 
            case Permanent: {
                if (s != Enum.XAntibodyState.Permanent && s != Enum.XAntibodyState.XProgram) break;
                this._xAntibodyState = s;
            }
        }
        this._xAntibodyCount = this._xAntibodyState != Enum.XAntibodyState.None ? Config._xAntibodyCountMax : 0;
    }

    public void setXAntibodyCount(int i) {
        if (i <= 0) {
            i = 0;
            this.setXAntibodyState(Enum.XAntibodyState.None);
        } else if (i > Config._xAntibodyCountMax) {
            i = Config._xAntibodyCountMax;
        }
        this._xAntibodyCount = i;
    }

    public ArrayList<Consumable> getFoodTypesAsConsumable(ArrayList<FoodType> f) {
        ArrayList<Consumable> list = new ArrayList<Consumable>();
        list.addAll(f);
        return list;
    }

    public ArrayList<Consumable> getFoodTypesAsConsumable() {
        return this.getFoodTypesAsConsumable(this._foodTypes);
    }

    public ArrayList<FoodType> getFoodTypes() {
        return this._foodTypes;
    }

    public DNA getDNA() {
        return this._dna;
    }

    public ArrayList<Consumable> getItemsAsConsumable(ArrayList<Item> i) {
        ArrayList<Consumable> list = new ArrayList<Consumable>();
        list.addAll(i);
        return list;
    }

    public ArrayList<Consumable> getItemsAsConsumable() {
        return this.getItemsAsConsumable(this._items);
    }

    public ArrayList<Item> getItems() {
        return this._items;
    }

    public ArrayList<Item> getShopItems() {
        ArrayList<Item> items = new ArrayList<Item>();
        for (Item item : this._items) {
            if (!item.getShopUnlocked() || item.getHomeShop().getPurchasePrice() <= 0) continue;
            items.add(item);
        }
        return items;
    }

    public ArrayList<Integer> getDailyTrophies() {
        return this._dailyTrophies;
    }

    public ArrayList<Integer> getFoughtTrophiesToday() {
        return this._foughtTrophiesToday;
    }

    public Tournament getTournament() {
        return this._tournament;
    }

    public int[] getTrophySchedule() {
        if (!this._isHome) {
            Town t = this._world.getCurrentZone().isTown();
            if (t != null) {
                return t.getTrophies(this);
            }
            return new int[0];
        }
        return this._trophySchedule;
    }

    public void setTrophySchedule() {
        this._trophySchedule = this._tournament.randTrophyIDs(this.getSeason(), this._trophySchedule, Config._forcedHomeTrophies);
    }

    public Enum.Food getMajorFood() {
        if (this._meatEaten > this._vegEaten && this._meatEaten > this._fruitEaten && this._meatEaten > this._fishEaten && this._meatEaten > this._junkEaten && this._meatEaten > this._medEaten && this._meatEaten > this._grainEaten && this._meatEaten > this._dairyEaten) {
            return Enum.Food.Meat;
        }
        if (this._vegEaten > this._meatEaten && this._vegEaten > this._fruitEaten && this._vegEaten > this._fishEaten && this._vegEaten > this._junkEaten && this._vegEaten > this._medEaten && this._vegEaten > this._grainEaten && this._vegEaten > this._dairyEaten) {
            return Enum.Food.Veg;
        }
        if (this._fruitEaten > this._meatEaten && this._fruitEaten > this._vegEaten && this._fruitEaten > this._fishEaten && this._fruitEaten > this._junkEaten && this._fruitEaten > this._medEaten && this._fruitEaten > this._grainEaten && this._fruitEaten > this._dairyEaten) {
            return Enum.Food.Fruit;
        }
        if (this._fishEaten > this._meatEaten && this._fishEaten > this._vegEaten && this._fishEaten > this._fruitEaten && this._fishEaten > this._junkEaten && this._fishEaten > this._medEaten && this._fishEaten > this._grainEaten && this._fishEaten > this._dairyEaten) {
            return Enum.Food.Fish;
        }
        if (this._junkEaten > this._meatEaten && this._junkEaten > this._vegEaten && this._junkEaten > this._fruitEaten && this._junkEaten > this._fishEaten && this._junkEaten > this._medEaten && this._junkEaten > this._grainEaten && this._junkEaten > this._dairyEaten) {
            return Enum.Food.Junk;
        }
        if (this._medEaten > this._meatEaten && this._medEaten > this._vegEaten && this._medEaten > this._fruitEaten && this._medEaten > this._fishEaten && this._medEaten > this._junkEaten && this._medEaten > this._grainEaten && this._medEaten > this._dairyEaten) {
            return Enum.Food.Med;
        }
        if (this._grainEaten > this._meatEaten && this._grainEaten > this._vegEaten && this._grainEaten > this._fruitEaten && this._grainEaten > this._fishEaten && this._grainEaten > this._junkEaten && this._grainEaten > this._medEaten && this._grainEaten > this._dairyEaten) {
            return Enum.Food.Grain;
        }
        if (this._dairyEaten > this._meatEaten && this._dairyEaten > this._vegEaten && this._dairyEaten > this._fruitEaten && this._dairyEaten > this._fishEaten && this._dairyEaten > this._junkEaten && this._dairyEaten > this._medEaten && this._dairyEaten > this._grainEaten) {
            return Enum.Food.Dairy;
        }
        return Enum.Food.None;
    }

    public Enum.Time getTrainTime() {
        Enum.Time time = Enum.Time.None;
        if (this._dayTrain > this._morningTrain && this._dayTrain > this._nightTrain) {
            time = Enum.Time.Noon;
        } else if (this._morningTrain > this._dayTrain && this._morningTrain > this._nightTrain) {
            time = Enum.Time.Morning;
        } else if (this._nightTrain > this._dayTrain && this._nightTrain > this._morningTrain) {
            time = Enum.Time.Night;
        }
        return time;
    }

    public int getDisposition() {
        return this._disposition;
    }

    public int getGlutton() {
        return this._glutton;
    }

    public int getRestless() {
        return this._restless;
    }

    public Enum.Personality getPersonality() {
        return this._personality;
    }

    public Enum.Food getFavFood() {
        return this._foodRanks.getFavorite();
    }

    public Enum.Food getDislikedFood() {
        return this._foodRanks.getDisliked();
    }

    public Enum.Attribute getFavAtt() {
        return this._attributeRanks.getFavorite();
    }

    public Enum.Attribute getDislikedAtt() {
        return this._attributeRanks.getDisliked();
    }

    public Enum.Time getFavTime() {
        return this._timeRanks.getFavorite();
    }

    public Enum.Time getDislikedTime() {
        return this._timeRanks.getDisliked();
    }

    public Enum.Food getFoodPreference() {
        return this._foodRanks.getPreference();
    }

    public Enum.Food getFoodAversion() {
        return this._foodRanks.getAversion();
    }

    public ArrayList<Enum.Food> getFoodIntolerance() {
        return this._foodRanks.getIntolerant();
    }

    public Enum.Time getTimePreference() {
        return this._timeRanks.getPreference();
    }

    public Enum.Time getTimeAversion() {
        return this._timeRanks.getAversion();
    }

    public Enum.Attribute getAttributePreference() {
        return this._attributeRanks.getPreference();
    }

    public Enum.Attribute getAttributeAversion() {
        return this._attributeRanks.getAversion();
    }

    public Taste getFoodRanks() {
        return this._foodRanks;
    }

    public Taste getTimeRanks() {
        return this._timeRanks;
    }

    public Taste getAttributeRanks() {
        return this._attributeRanks;
    }

    public void setClock(CurrentTime newClock) {
        this._clock = newClock;
    }

    public CurrentTime getClock() {
        return this._clock;
    }

    public Enum.Weather getCurrentWeather() {
        return this._currentWeather;
    }

    public boolean getRefused() {
        return this._refused;
    }

    public void setRefused(boolean newRefused) {
        this._refused = newRefused;
    }

    public boolean getCompliance() {
        return this._compliance;
    }

    public void setCompliance(boolean newCompliance) {
        if (this._compliance && !newCompliance) {
            this._praise = true;
        }
        this._compliance = newCompliance;
    }

    public Evolution getEvolution() {
        return this._evolution;
    }

    public int[] getTempRecord() {
        return this._tempRecord;
    }

    public int[] getObedienceRecord() {
        return this._obedienceRecord;
    }

    public byte getTemp() {
        return this._temp;
    }

    public void setTemp(int temp) {
        if (temp < 0) {
            temp = 0;
        } else if (temp > Config._maxTemp) {
            temp = Config._maxTemp;
        }
        this._temp = (byte)temp;
    }

    public void setDayTemp() {
        Random r = new Random();
        this._dayTemp = (byte)r.nextInt(Config._randomDaysTemp);
        int i = 0;
        Habitat habitat = this._habitats.get(this._currentHabitat);
        try {
            switch (this.getSeason()) {
                case Spring: {
                    i = habitat.getSpringTemp()[0] + r.nextInt(habitat.getSpringTemp()[1] - habitat.getSpringTemp()[0] + 1);
                    break;
                }
                case Fall: {
                    i = habitat.getFallTemp()[0] + r.nextInt(habitat.getFallTemp()[1] - habitat.getFallTemp()[0] + 1);
                    break;
                }
                case Summer: {
                    i = habitat.getSummerTemp()[0] + r.nextInt(habitat.getSummerTemp()[1] - habitat.getSummerTemp()[0] + 1);
                    break;
                }
                case Winter: {
                    i = habitat.getWinterTemp()[0] + r.nextInt(habitat.getWinterTemp()[1] - habitat.getWinterTemp()[0] + 1);
                }
            }
            this._dayTemp = (byte)i;
        }
        catch (IllegalArgumentException e) {
            this._dayTemp = 0;
        }
    }

    public int getDayTemp() {
        return this._dayTemp;
    }

    public void setTempGoal(int temp) {
        if (temp >= 0 && temp <= Config._maxTemp) {
            this._tempGoal = (byte)temp;
        }
    }

    public byte getTempGoal() {
        return this._tempGoal;
    }

    public byte[] getIdealTemp() {
        return this._idealTemp;
    }

    public void setIdealTemp(byte[] temp) {
        this._idealTemp[0] = temp[0];
        this._idealTemp[1] = temp[1];
    }

    public void setDay(int newDay) {
        if (newDay > Config._maxFastClockDays) {
            newDay = 0;
        }
        this._day = newDay;
    }

    public int getDay() {
        return this._day;
    }

    public Enum.Season getSeason() {
        Enum.Season season = Enum.Season.Spring;
        if (this._clock != null && !this._timeSkip) {
            season = this._day >= Config._firstSpringDay && this._day < Config._firstSummerDay ? Enum.Season.Spring : (this._day >= Config._firstSummerDay && this._day < Config._firstFallDay ? Enum.Season.Summer : (this._day >= Config._firstFallDay && this._day < Config._firstWinterDay ? Enum.Season.Fall : Enum.Season.Winter));
        } else if (this._clock != null) {
            Calendar currentDate = Calendar.getInstance();
            int month = currentDate.get(2) + 1;
            season = month >= Config._firstSpringMonth && month < Config._firstSummerMonth ? Enum.Season.Spring : (month >= Config._firstSummerMonth && month < Config._firstFallMonth ? Enum.Season.Summer : (month >= Config._firstFallMonth && month < Config._firstWinterMonth ? Enum.Season.Fall : Enum.Season.Winter));
        }
        return season;
    }

    public void setSaveString(String newSave) {
        this._saveString = newSave;
    }

    public String getSaveString() {
        return this._saveString;
    }

    public boolean getLoading() {
        return this._loading;
    }

    public int getSpriteNum() {
        return this._spriteNum;
    }

    public void setSpriteNum(int newNum) {
        this._spriteNum = newNum;
    }

    public int getSpriteSet() {
        return this._spriteSet;
    }

    public void setSpriteSet(int newSet) {
        this._spriteSet = newSet;
    }

    public Enum.State getCurrentState() {
        return this._currentState;
    }

    public void setCurrentState(Enum.State newState) {
        if (this.queueState(newState)) {
            this.addToQueue(newState);
        } else {
            this._currentState = newState;
        }
    }

    public void forceQueue(Enum.State s) {
        if (!Utility.containsState(Utility.ENABLE_DURING_STATE, s)) {
            this.addToQueue(s);
        }
    }

    public void setStateNoRepeat(Enum.State s) {
        if (this._currentState != s && !this._animQueue.contains((Object)s)) {
            this.setCurrentState(s);
        }
    }

    public void setPriorityState(Enum.State s) {
        if (this.queueState(s)) {
            this.prioritizeStateInQueue(s);
        } else {
            this._currentState = s;
        }
    }

    public void forceState(Enum.State s) {
        this.setPriorityState(this._currentState);
        this._currentState = s;
    }

    private boolean queueState(Enum.State newState) {
        return !Utility.containsState(Utility.ENABLE_DURING_STATE, this._currentState) && !Utility.containsState(Utility.ENABLE_DURING_STATE, newState);
    }

    public ArrayList getAnimQueue() {
        return this._animQueue;
    }

    public int getAge() {
        return this._age;
    }

    public void setAge(int newAge) {
        if (newAge >= 0) {
            this._age = newAge;
        }
    }

    public int getBonus() {
        return this._bonus;
    }

    public void setBonus(int newBonus) {
        this._bonus = newBonus;
    }

    public int getTimeToAge() {
        return this._timeToAge;
    }

    public void setTimeToAge(int newTimeToAge) {
        if (newTimeToAge >= 0) {
            this._timeToAge = newTimeToAge;
        }
        if (this._timeToAge >= Config._ageUp) {
            this._timeToAge = 0;
            this.setAge(this._age + 1);
            Enum.Mood m = this.getMajorMood(this._dailyMoodRecord);
            for (int i = 0; i < this._dailyMoodRecord.length; ++i) {
                this._dailyMoodRecord[i] = 0;
            }
            if (this._mistakeDay <= Config._maxMistakeDayForBonusInc && m == Enum.Mood.Happy) {
                this.setTotalLifespan(this._totalLifespan + (long)Config._bonusLifeInc);
                ++this._bonus;
                this._foodTypes.get(Config._goodBirthdayFood).incQuantity();
                this._unlockConsumable = Config._goodBirthdayFood;
                if (this._asleep) {
                    this.setCurrentState(Enum.State.NormalMorning);
                }
                this.setCurrentState(Enum.State.Birthday_Good);
            } else if (m == Enum.Mood.Unhappy && this._mistakeDay >= Config._minMistakeDayForBonusDec) {
                this.setTotalLifespan(this._totalLifespan - (long)Config._bonusLifeDec);
                if (this._bonus > 0) {
                    --this._bonus;
                }
                this._foodTypes.get(Config._badBirthdayFood).incQuantity();
                this._unlockConsumable = Config._badBirthdayFood;
                if (this._asleep) {
                    this.setCurrentState(Enum.State.NormalMorning);
                }
                this.setCurrentState(Enum.State.Birthday_Bad);
            } else {
                this._foodTypes.get(Config._normalBirthdayFood).incQuantity();
                this._unlockConsumable = Config._normalBirthdayFood;
                if (this._asleep) {
                    this.setCurrentState(Enum.State.NormalMorning);
                }
                this.setCurrentState(Enum.State.Birthday_Normal);
            }
            this._mistakeDay = 0;
            this.autoSave();
        }
    }

    public int getCallMinutesPoop() {
        return this._callMinutesPoop;
    }

    public int getCallMinutesHunger() {
        return this._callMinutesHunger;
    }

    public int getCallMinutesStrength() {
        return this._callMinutesStrength;
    }

    public int getCallMinutesLights() {
        return this._callMinutesLights;
    }

    public int getCallMinutesDiscipline() {
        return this._callMinutesDiscipline;
    }

    private void resetAllCallMinutes() {
        this._callMinutesPoop = 0;
        this._callMinutesHunger = 0;
        this._callMinutesStrength = 0;
        this._callMinutesLights = 0;
        this._callMinutesDiscipline = 0;
    }

    private boolean hungerCall() {
        return this._alive && !this._asleep && this._hunger <= 0;
    }

    private boolean strengthCall() {
        return this._alive && !this._asleep && this._exercise <= 0;
    }

    private boolean poopCall() {
        return this._alive && !this._asleep && this.countFilth() >= Config._mistakeFilthLimit;
    }

    private boolean lightsCall() {
        return this._alive && this._asleep && this._lights;
    }

    private boolean disciplineCall() {
        return this._alive && !this._asleep && this._disciplineCall;
    }

    public int scaleToClock(int value) {
        return value * (Config._enableFastForward ? 1 : this._clock.getFastMod());
    }

    private void incCallMinutes() {
        if (this.poopCall()) {
            ++this._callMinutesPoop;
            if (this._callMinutesPoop >= this.scaleToClock(Config._minutesToMistakePoop)) {
                this._callMinutesPoop = this.scaleToClock(Config._afterMistakeMinutesPostponed);
                this.incMistake();
            }
        }
        if (this.hungerCall()) {
            ++this._callMinutesHunger;
            if (this._callMinutesHunger >= this.scaleToClock(Config._minutesToMistakeHunger)) {
                this._callMinutesHunger = this.scaleToClock(Config._afterMistakeMinutesPostponed);
                this.incMistake();
                this.hungerMistakePenalty();
            }
        }
        if (this.strengthCall()) {
            ++this._callMinutesStrength;
            if (this._callMinutesStrength >= this.scaleToClock(Config._minutesToMistakeStrength)) {
                this._callMinutesStrength = this.scaleToClock(Config._afterMistakeMinutesPostponed);
                this.strengthMistakePenalty();
                this.incMistake();
            }
        }
        if (this.lightsCall()) {
            ++this._callMinutesLights;
            if (this._callMinutesLights >= this.scaleToClock(Config._minutesToMistakeLights)) {
                this._callMinutesLights = this.scaleToClock(Config._afterMistakeMinutesPostponed);
                if (!this._lightsOffMistake) {
                    boolean bl = this._lightsOffMistake = this._asleep && this._lights;
                    if (this._lightsOffMistake) {
                        this.setObedience(this._obedience + Config._lightsOnMistakeObedienceChange);
                    }
                }
                this.incMistake();
            }
        }
        if (this.disciplineCall()) {
            ++this._callMinutesDiscipline;
            if (this._callMinutesDiscipline >= this.scaleToClock(Config._minutesToDisciplinePenalty)) {
                this._callMinutesDiscipline = 0;
                this._disciplineCall = false;
                this.setMood(this._mood - Config._disciplineCallMoodPenalty);
                this._mistakeDay += Config._disciplineCallFailMistakeDayChange;
            }
        }
    }

    public boolean getPraise() {
        return this._praise;
    }

    public void setPraise(boolean newPraise) {
        this._praise = newPraise;
    }

    public void setPraiseWindow(byte newWindow) {
        this._praiseWindow = newWindow;
        if (this._praiseWindow >= this.scaleToClock(Config._maxPraiseWindow)) {
            this._praiseWindow = 0;
            this.setMood(this._mood - Config._praiseFailMoodPenalty);
            this.setObedience(this._obedience + (this._disposition > 0 ? Config._praiseFailObedienceInc : Config._praiseFailObedienceInc + this._disposition * Config._praiseFailObedienceIncDispositionCoefficient));
            this._praise = false;
        } else if (this._praiseWindow == 0) {
            this._praise = false;
        }
    }

    public boolean getScold() {
        return this._scold;
    }

    public void setScold(boolean newScold) {
        this._scold = newScold;
    }

    public void setScoldWindow(byte newWindow) {
        this._scoldWindow = newWindow;
        if (this._scoldWindow >= this.scaleToClock(Config._maxScoldWindow)) {
            this._scoldWindow = 0;
            this._refused = false;
            this.setMood(this._mood + Config._scoldFailMoodInc);
            this.setObedience(this._obedience - Config._scoldFailObediencePenalty);
            this._scold = false;
        } else if (this._scoldWindow == 0) {
            this._scold = false;
        }
    }

    public int getMood() {
        return this._mood;
    }

    public void setMood(int newMood) {
        if (newMood != this._mood) {
            newMood += this._disposition * Config._moodChangeDispositionCoefficient;
        }
        if (newMood < Config._minMood) {
            newMood = Config._minMood;
        } else if (newMood > Config._maxMood) {
            newMood = Config._maxMood;
        }
        this._mood = newMood;
        if (this._currentMood != Enum.Mood.Depressed) {
            this.setCurrentMood();
        }
    }

    public Enum.Mood getCurrentMood() {
        return this._currentMood;
    }

    private void setCurrentMood() {
        this._currentMood = this._mood >= Config._minHappyMood ? Enum.Mood.Happy : (this._mood <= Config._minUnhappyMood ? Enum.Mood.Unhappy : Enum.Mood.Neutral);
    }

    public byte getEnthusiasm() {
        return this._enthusiasm;
    }

    public void setEnthusiasm(byte newEnthusiasm) {
        if (newEnthusiasm != this._enthusiasm) {
            Random ran = new Random();
            int r = ran.nextInt(Config._lessEnthusiasmChance) + this._restless * Config._enthusiasmChangeRestlessCoefficient;
            if (r < 0) {
                newEnthusiasm = (byte)(newEnthusiasm - 1);
            } else if (r > 4) {
                newEnthusiasm = (byte)(newEnthusiasm + 1);
            }
        }
        if (newEnthusiasm < Config._minEnthusiasm) {
            newEnthusiasm = Config._minEnthusiasm;
        } else if (newEnthusiasm > Config._maxEnthusiasm) {
            newEnthusiasm = Config._maxEnthusiasm;
        }
        if ((newEnthusiasm == Config._maxEnthusiasm || newEnthusiasm == Config._minEnthusiasm) && this._enthusiasm == newEnthusiasm) {
            this.setMood(this._mood - Config._maxEnthusiasmMoodPenalty);
        }
        this._enthusiasm = newEnthusiasm;
    }

    public byte getItemInterest() {
        return this._itemInterest;
    }

    public void setItemInterest(byte i) {
        this._itemInterest = i > Config._maxItemInterest ? Config._maxItemInterest : (i < 0 ? (byte)0 : i);
    }

    public int getObedience() {
        return this._obedience;
    }

    public void setObedience(int newObedience) {
        if (newObedience != this._obedience) {
            newObedience -= this._disposition * Config._obedienceChangeDispositionCoefficient;
        }
        if (newObedience < 0) {
            newObedience = 0;
        } else if (newObedience > Config._maxObedience) {
            newObedience = Config._maxObedience;
        }
        this._obedience = newObedience;
    }

    public byte getSurrender() {
        return this._surrender;
    }

    public void setSurrender(byte s) {
        this._surrender = s;
    }

    private boolean isToiletTrained() {
        return Config._minToiletUsesToTrain <= this._toiletTrained && this._obedience >= Config._toiletTrainedObedienceMin && Config._stageCanAutoToilet.contains((Object)this._growthStage);
    }

    public void toiletTrain() {
        if (this._toiletTrained < Config._minToiletUsesToTrain && Config._stageCanToiletTrain.contains((Object)this._growthStage)) {
            this._toiletTrained = (byte)(this._toiletTrained + 1);
        }
    }

    public byte getHunger() {
        return this._hunger;
    }

    public void setHunger(byte newHunger) {
        this.setHunger(newHunger, null, false);
    }

    public void setHunger(byte newHunger, FoodType food, boolean complied) {
        if (this._alive && this._growthStage != Enum.Stage.Egg && newHunger != this._hunger && !this.pauseHunger()) {
            int stomachCapacity;
            boolean old = this.isGeriatric();
            if (newHunger > 0) {
                this._callMinutesHunger = 0;
            }
            if (newHunger < this._hunger) {
                this.changeNutrition(Config._nutritionLapseChange);
                this.calorieChange(old);
                if (old) {
                    this.setWeight(this._weight + Config._geriatricWeightChangeOnHungerDecay);
                }
            }
            if (newHunger < 0 && this._hunger == 0) {
                this.setCaloriesAndChangeWeight(this._calories + Config._starvationCalorieChange);
                this._mistakeDay += Config._hungerDecAtZeroMistakeDayChange;
                if (old) {
                    this.setTotalLifespan(this._totalLifespan + (long)Config._geriatricHungerDecayAtZeroLifespanChange);
                }
            }
            if (newHunger >= this.getOvereatLimit(stomachCapacity = this.getStomachCapacity()) && newHunger > this._hunger) {
                this.overeatPenalty(food, complied);
                if (newHunger == stomachCapacity) {
                    this._hunger = (byte)stomachCapacity;
                } else if (newHunger > stomachCapacity) {
                    this.stomachCapacityPenalty(newHunger, food, complied);
                } else {
                    this._hunger = newHunger;
                }
            } else {
                this._hunger = newHunger < 0 ? (byte)0 : newHunger;
            }
        }
    }

    private void calorieChange(boolean old) {
        int calories = Config._calorieLapseChange;
        if (this._asleep) {
            calories = Config._calorieLapseChangeAsleep;
            if (old) {
                calories += Config._calorieLapseChangeGeriatricAsleep;
            }
        } else if (old) {
            calories += Config._calorieLapseChangeGeriatric;
        }
        this.setCalories(this._calories + calories);
    }

    private boolean pauseHunger() {
        boolean pause = false;
        for (CareEffect e : this._careEffects) {
            if (!e.isActive() || !e.pauseHunger()) continue;
            pause = true;
            break;
        }
        return pause;
    }

    public void setRawHunger(int newHunger) {
        if (newHunger > 0) {
            this._callMinutesHunger = 0;
        }
        this._hunger = (byte)newHunger;
    }

    public int getOvereatLimit() {
        return this.getOvereatLimit(this.getStomachCapacity());
    }

    public int getOvereatLimit(double stomachCapacity) {
        return (int)(stomachCapacity * Config._overeatLimit);
    }

    public void setStomachCapacity(int newCapacity) {
        this._stomachCapacity = (byte)newCapacity;
    }

    public int getStomachCapacity() {
        if (this.isGeriatric()) {
            int dec;
            long lifeRemainder = this._totalLifespan - this._lapsedLife;
            long diff = (long)Config._geriatricAge - lifeRemainder;
            if (diff < 0L) {
                diff = 0L;
            }
            if (this._stomachCapacity - (dec = (int)((double)diff * Config._geriatricStomachCapacityPenaltyCoefficient)) < Config._minStomachCapacity) {
                return Config._minStomachCapacity;
            }
            return this._stomachCapacity - dec;
        }
        return this._stomachCapacity;
    }

    public int getExerciseLimit() {
        if (this.isGeriatric()) {
            int dec;
            long lifeRemainder = this._totalLifespan - this._lapsedLife;
            long diff = (long)Config._geriatricAge - lifeRemainder;
            if (diff < 0L) {
                diff = 0L;
            }
            if (this._exerciseLimit - (dec = (int)((double)diff * Config._geriatricMaxStrengthPenaltyCoefficient)) < Config._minStrengthLimit) {
                return Config._minStrengthLimit;
            }
            return this._exerciseLimit - dec;
        }
        return this._exerciseLimit;
    }

    public byte getExercise() {
        return this._exercise;
    }

    public void setExercise(byte newExercise) {
        this.setExercise(newExercise, null, 0, false);
    }

    public void setExercise(byte newExercise, Enum.Attribute a, int moodRankChange, boolean complied) {
        if (this._alive && this._growthStage != Enum.Stage.Egg && newExercise != this._exercise && !this.pauseStrength()) {
            if (newExercise > 0) {
                this._callMinutesStrength = 0;
            }
            if (newExercise < 0 && this._exercise == 0) {
                this._mistakeDay += Config._strengthDecAtZeroMistakeDayChange;
            }
            if (newExercise >= this.getExerciseLimit()) {
                if (newExercise > this._exercise) {
                    Habitat h = this.getCurrentHabitat();
                    int change = (this.compatibleElement(this._element, h) ? Config._compatibleElementFatigueChanceChange : (byte)0) + (this.compatibleField(this._field, h) ? Config._compatibleFieldFatigueChanceChange : (byte)0) + (this.incompatibleField(this._field, h) ? Config._incompatibleFieldFatigueChanceChange : (byte)0) + (this.incompatibleElement(this._element, h) ? Config._incompatibleElementFatigueChanceChange : (byte)0);
                    Random r = new Random();
                    int p = r.nextInt(100);
                    if (p < (this.getGoodNutrition() ? Config._goodNutritionFatigueChance + change : Config._fatigueChance + change)) {
                        this.fatigue(a, moodRankChange, complied);
                    }
                }
                newExercise = (byte)this.getExerciseLimit();
            }
            if (newExercise < 0) {
                newExercise = 0;
            }
            this._exercise = this._energy <= 0 && newExercise <= 0 && this._exercise > newExercise ? (byte)1 : newExercise;
        }
    }

    public void setRawExercise(int newExercise) {
        if (newExercise >= 0 && newExercise <= this.getExerciseLimit()) {
            this._callMinutesStrength = 0;
            this._exercise = (byte)newExercise;
        }
    }

    private boolean pauseStrength() {
        boolean pause = false;
        for (CareEffect e : this._careEffects) {
            if (!e.isActive() || !e.pauseStrength()) continue;
            pause = true;
            break;
        }
        return pause;
    }

    public byte getMaxEnergy() {
        return this._maxEnergy;
    }

    public byte getEnergy() {
        return this._energy;
    }

    public void setEnergy(byte newEnergy) {
        if (this._energy > newEnergy && newEnergy < 0) {
            this.setMood(this._mood - (Config._negativeEnergyMoodDec - 1 * newEnergy));
            this.setObedience(this._obedience - (Config._negativeEnergyObedienceDec - 1 * newEnergy));
            if (newEnergy < 0 && !this.isInj()) {
                this.fatigue(false);
            }
        }
        if ((newEnergy = this.checkEnergyIncFromPerfectConditions(newEnergy)) > this._maxEnergy) {
            this._energy = this._maxEnergy;
        } else if (newEnergy < -this._maxEnergy) {
            this._energy = -this._maxEnergy;
            this.setTotalLifespan(this._totalLifespan - (long)Config._minEnergyLifePenalty);
            if (Config._enableLifePenaltyAnim) {
                this.setStateNoRepeat(Enum.State.Bad_Health_Jeering);
            }
        } else {
            this._energy = newEnergy;
        }
    }

    public byte checkEnergyIncFromPerfectConditions(byte newEnergy) {
        if (newEnergy < this._energy && this.getFavTime() == this.checkTime(this._clock.getHours())) {
            Habitat h = this.getCurrentHabitat();
            int change = 0;
            change += (this.compatibleElement(this._element, h) ? Config._compatibleElementEnergyBonusChanceChange : (byte)0) + (this.compatibleField(this._field, h) ? Config._compatibleFieldEnergyBonusChanceChange : (byte)0) + (this.incompatibleField(this._field, h) ? Config._incompatibleFieldEnergyBonusChanceChange : (byte)0) + (this.incompatibleElement(this._element, h) ? Config._incompatibleElementEnergyBonusChanceChange : (byte)0);
            change += this._currentWeather == Enum.Weather.Clear || this._currentWeather == Enum.Weather.Cloudy || this.checkNiceWeather(this.checkIsRain()) ? Config._energyBonusChanceGoodWeather : (byte)0;
            change += this._currentMood == Enum.Mood.Happy ? Config._energyBonusChanceGoodMood : (byte)0;
            change += this._temp >= this._idealTemp[0] && this._temp <= this._idealTemp[1] ? (int)Config._energyBonusChanceGoodTemp : 0;
            Random random = new Random();
            int prob = random.nextInt(Config._bonusEnergyIncChance + (change += this.getGoodNutrition() ? Config._energyBonusChanceGoodNutrition : (byte)0));
            if (prob == 1) {
                newEnergy = (byte)(newEnergy + 1);
            }
        }
        return newEnergy;
    }

    public int getWeight() {
        return this._weight;
    }

    public void setWeight(int newWeight) {
        double max = this.getWeightMax();
        double min = this.getWeightMin();
        if ((double)newWeight < min) {
            this._weight = (int)min;
            this.weightLimitPenalty();
        } else if ((double)newWeight > max) {
            this._weight = (int)max;
            this.weightLimitPenalty();
        } else {
            this._weight = newWeight <= 0 ? 1 : newWeight;
        }
        this.checkOverweight();
    }

    private double getWeightMax() {
        return (long)this._baseWeight + Math.round((double)this._baseWeight * Config._weightLimitMultiple);
    }

    private double getWeightMin() {
        return (long)this._baseWeight - Math.round((double)this._baseWeight * Config._weightLimitMultiple);
    }

    public int getBaseWeight() {
        return this._baseWeight;
    }

    public void setBaseWeight(int newBase) {
        this._baseWeight = newBase;
    }

    public int getMaxCalories() {
        return Config._calorieLimit + this._calorieMaxMod + (this._overweight == Enum.Weight.Over ? Config._calorieLimitModWeight : (byte)0);
    }

    public int getMinCalories() {
        return -Config._calorieLimit - this._calorieMinMod - (this._overweight == Enum.Weight.Under ? Config._calorieLimitModWeight : (byte)0);
    }

    public int getCalories() {
        return this._calories;
    }

    public void setCalories(int c) {
        int max = this.getMaxCalories();
        int min = this.getMinCalories();
        if (c > max) {
            if (this._calories < c) {
                this._bmGauge += Config._aboveMaxCaloriesBMGaugeChange;
            }
            this._calories = max;
        } else if (c < min) {
            if (this._calories > c) {
                this._hungerDecayLapse = (byte)(this._hungerDecayLapse + Config._belowMinCaloriesHungerLapseChange);
            }
            this._calories = min;
        } else {
            this._calories = c;
        }
    }

    public void setCaloriesAndChangeWeight(int newCalories) {
        if (newCalories > this._calories && this._calories > 0) {
            this.setWeight(this._weight + Config._foodWeightChange);
        } else if (newCalories < this._calories && this._calories < 0) {
            this.setWeight(this._weight + Config._activityWeightChange);
        }
        this.setCalories(newCalories);
    }

    public int getBMGauge() {
        return this._bmGauge;
    }

    public void setBMGauge(int newBMGauge) {
        this._bmGauge = newBMGauge < 0 ? 0 : newBMGauge;
    }

    public byte getBMMax() {
        return this._bmMax;
    }

    public int getMistake() {
        return this._mistake;
    }

    public boolean getAsleep() {
        return this._asleep;
    }

    public void setAsleep(boolean newAsleep) {
        this.setAsleep(newAsleep, true);
    }

    public void setAsleep(boolean newAsleep, boolean wakeAnim) {
        if (this._asleep && !newAsleep) {
            Random ran = new Random();
            int r = ran.nextInt(Config._morningMoodChance);
            Enum.State s = Enum.State.NormalMorning;
            if (!this._nap) {
                if (r == 0) {
                    s = Enum.State.BadMorning;
                    switch (this._currentMood) {
                        case Unhappy: {
                            this.setMood(this._mood + Config._badMorningUnhappyMoodChange);
                            break;
                        }
                        case Neutral: {
                            this.setMood(this._mood + Config._badMorningNeutralMoodChange);
                            break;
                        }
                        case Happy: {
                            this.setMood(this._mood + Config._badMorningHappyMoodChange);
                        }
                    }
                } else if (r == 1) {
                    if (this._currentMood.equals((Object)Enum.Mood.Happy)) {
                        this.setMood(Config._worstMorningMood);
                        s = Enum.State.TerribleMorning;
                    }
                } else if (r == 2) {
                    s = Enum.State.GoodMorning;
                    switch (this._currentMood) {
                        case Unhappy: {
                            this.setMood(this._mood + Config._goodMorningUnhappyMoodChange);
                            break;
                        }
                        case Neutral: {
                            this.setMood(this._mood + Config._goodMorningNeutralMoodChange);
                            break;
                        }
                        case Happy: {
                            this.setMood(this._mood + Config._goodMorningHappyMoodChange);
                        }
                    }
                }
            } else {
                switch (r) {
                    case 0: {
                        this.setMood(this._mood + Config._napWakeMoodChange * -1);
                        s = Enum.State.BadMorning;
                        break;
                    }
                    case 1: {
                        this.setMood(this._mood + Config._napWakeMoodChange * 1);
                        s = Enum.State.GoodMorning;
                        break;
                    }
                }
            }
            if (wakeAnim && this._currentState != Enum.State.Jeering && this._currentState != Enum.State.Sad_Jeering && !this._animQueue.contains((Object)Enum.State.Jeering) && !this._animQueue.contains((Object)Enum.State.Sad_Jeering)) {
                this.setPriorityState(s);
            }
        } else if (!this._asleep && newAsleep) {
            this._callMinutesLights = 0;
        }
        this.checkEffectSleepEnd();
        this._asleep = newAsleep;
        if (!this._asleep) {
            this._nap = false;
        }
        this._lightsOffMistake = false;
    }

    private void checkEffectSleepEnd() {
        for (CareEffect e : this._careEffects) {
            if (!e.endOnSleepChange()) continue;
            e.setLapse(0);
        }
    }

    public boolean getLights() {
        return this._lights;
    }

    public void setLights(boolean newLights) {
        this._lightsOffMistake = false;
        this._lights = newLights;
    }

    public boolean setAutoCare(boolean b) {
        this._autoCare = b;
        if (b) {
            this._assistantID = this._evolution.getRandomAssistDigimon();
        }
        return this._autoCare;
    }

    public boolean getAutoCare() {
        return this._autoCare;
    }

    private boolean doAutoCare() {
        if (this._alive && this._isHome && this._canEvolveOrDie && this._autoCare) {
            this._autoCare = this._bits >= this.getAutoCarePrice();
        }
        return this._alive && this._isHome && this._canEvolveOrDie && this._autoCare;
    }

    private int getAutoCarePrice() {
        int price = 0;
        switch (this._growthStage) {
            case Egg: {
                price = Config._autoCareStageIPrice;
                break;
            }
            case Fresh: {
                price = Config._autoCareStageIPrice;
                break;
            }
            case InTraining: {
                price = Config._autoCareStageIIPrice;
                break;
            }
            case Rookie: {
                price = Config._autoCareStageIIIPrice;
                break;
            }
            case Champion: {
                price = Config._autoCareStageIVPrice;
                break;
            }
            case Ultimate: {
                price = Config._autoCareStageVPrice;
                break;
            }
            case Mega: {
                price = Config._autoCareStageVIPrice;
            }
        }
        return price;
    }

    public int processAutoCarePrice() {
        int price = this.getAutoCarePrice();
        if (this._bits >= price) {
            this.setBits(this._bits - price);
            this.setMood(this._mood + Config._autoCareMoodChange);
            this.setObedience(this._obedience + Config._autoCareObedienceChange);
            this.setEnthusiasm((byte)(this._enthusiasm + Config._autoCareEnthusiasmChange));
        }
        return price;
    }

    public int getAssistantID() {
        return this._assistantID;
    }

    public void setTourneyAlarm(int i) {
        this._tourneyAlarm = i;
    }

    public int getTourneyAlarm() {
        return this._tourneyAlarm;
    }

    public boolean poopable() {
        return this._isHome && !this._tournament.getActive();
    }

    public int countFilth() {
        int c = 0;
        if (this.poopable()) {
            for (int i = 0; i < this._filth.length; ++i) {
                if (this._filth[i] <= 0) continue;
                ++c;
            }
        }
        return c;
    }

    public boolean isFilth() {
        return this.poopable() && this._filth[0] > 0;
    }

    public byte[] getFilth() {
        return this._filth;
    }

    public void addFilth(int f) {
        if (this.poopable()) {
            boolean added = false;
            if (f > 0 && f < 5) {
                int i;
                for (i = 0; i < this._filth.length; ++i) {
                    if (this._filth[i] != 0) continue;
                    this._filth[i] = (byte)f;
                    added = true;
                    break;
                }
                if (!added) {
                    for (i = 0; i < this._filth.length; ++i) {
                        if (this._filth[i] >= f) continue;
                        this._filth[i] = (byte)f;
                        break;
                    }
                }
            }
        }
    }

    public void clearFilth() {
        if (this.poopable()) {
            for (int i = 0; i < this._filth.length; ++i) {
                this._filth[i] = 0;
            }
            this._callMinutesPoop = 0;
        }
    }

    public int getDisturb() {
        return this._disturb;
    }

    public void setDisturb(int newDisturb) {
        this._disturb = newDisturb < 0 ? 0 : newDisturb;
    }

    public void setDifficultySetting(int b) {
        this._difficultySetting = b;
    }

    public int getDifficultySetting() {
        return this._difficultySetting;
    }

    public int getOvereat() {
        return this._overeat;
    }

    public Enum.Weight getOverweight() {
        return this._overweight;
    }

    public long getTotalLifespan() {
        return this._totalLifespan;
    }

    public void setTotalLifespan(long newTotalLifespan) {
        this.setTotalLifespan(newTotalLifespan, true);
    }

    public void setTotalLifespan(long newTotalLifespan, boolean enableNutrition) {
        if (newTotalLifespan < this._totalLifespan && enableNutrition && this.getGoodNutrition()) {
            long l = this._totalLifespan - newTotalLifespan;
            newTotalLifespan = this._totalLifespan - (long)((double)l * Config._goodNutritionLifespanDecCoefficient);
        }
        if (newTotalLifespan < this._lapsedLife + (long)Config._instantDeathGracePeriod) {
            newTotalLifespan = this._lapsedLife + (long)Config._instantDeathGracePeriod;
        }
        if (newTotalLifespan < 0L) {
            newTotalLifespan = 0L;
        } else if (newTotalLifespan > Config._maxLifespan) {
            newTotalLifespan = Config._maxLifespan;
        }
        this._totalLifespan = newTotalLifespan;
    }

    public long getLapsedLife() {
        return this._lapsedLife;
    }

    public void setLapsedLife(long newLapsedLife) {
        if (newLapsedLife >= 0L) {
            this._lapsedLife = newLapsedLife;
        }
        if (this._canEvolveOrDie && (this._lapsedLife >= this._totalLifespan || this._lapsedLife < 0L && this._currentState != Enum.State.Dying && !this._animQueue.contains((Object)Enum.State.Dying) || this._postponeDie)) {
            if (this._alive) {
                this.setAsleep(false, false);
                this._postponeDie = false;
                this._lapsedLife = Integer.MIN_VALUE;
                if (!this._isHome) {
                    this.setCurrentState(Enum.State.Teleport_Leave);
                }
                this.setCurrentState(Enum.State.Dying);
            }
        } else if (!this._canEvolveOrDie && this._lapsedLife == this._totalLifespan) {
            this._postponeDie = true;
            this._postponeEvolve = false;
        } else if (!this._postponeDie) {
            if (this._canEvolveOrDie && (this._lapsedLife == this._growthPeriod || this._postponeEvolve)) {
                this.evol(false, false);
                this._postponeEvolve = false;
            } else if (!this._canEvolveOrDie && this._lapsedLife == this._growthPeriod) {
                this._postponeEvolve = true;
            }
        }
    }

    public void saveFromDeath() {
        this._animQueue.clear();
        this._savedFromDeath = (byte)(this._savedFromDeath + 1);
        this._hunger = Config._hungerAfterSavedFromDeath;
        this._bonus += Config._bonusChangeAfterSavedFromDeath;
        this._lapsedLife = this._totalLifespan - (long)Config._revivalLifeInc;
        this.evol(true, false);
    }

    public int getVaccinePower() {
        return this._vaccinePower;
    }

    public void setVaccinePower(int newVaccinePower) {
        this._vaccinePower = newVaccinePower < 0 ? 0 : (newVaccinePower - this._vaccinePower == 1 && (this._attribute == Enum.Attribute.Vaccine || this._attribute == Enum.Attribute.None && this._growthStage != Enum.Stage.Fresh && this._growthStage != Enum.Stage.InTraining && this.getFavAtt() == Enum.Attribute.Vaccine) && this._currentMood == Enum.Mood.Happy ? newVaccinePower + Config._bonusAttributePower : newVaccinePower);
    }

    public int getDataPower() {
        return this._dataPower;
    }

    public void setDataPower(int newDataPower) {
        this._dataPower = newDataPower < 0 ? 0 : (newDataPower - this._dataPower == 1 && (this._attribute == Enum.Attribute.Data || this._attribute == Enum.Attribute.None && this._growthStage != Enum.Stage.Fresh && this._growthStage != Enum.Stage.InTraining && this.getFavAtt() == Enum.Attribute.Data) && this._currentMood == Enum.Mood.Happy ? newDataPower + Config._bonusAttributePower : newDataPower);
    }

    public int getVirusPower() {
        return this._virusPower;
    }

    public void setVirusPower(int newVirusPower) {
        this._virusPower = newVirusPower < 0 ? 0 : (newVirusPower - this._virusPower == 1 && (this._attribute == Enum.Attribute.Virus || this._attribute == Enum.Attribute.None && this._growthStage != Enum.Stage.Fresh && this._growthStage != Enum.Stage.InTraining && this.getFavAtt() == Enum.Attribute.Virus) && this._currentMood == Enum.Mood.Happy ? newVirusPower + Config._bonusAttributePower : newVirusPower);
    }

    public Enum.Attribute getAttribute() {
        return this._attribute;
    }

    public void setAttribute(Enum.Attribute newAttribute) {
        this._attribute = newAttribute;
    }

    public Enum.Element getElement() {
        return this._element;
    }

    public void setElement(Enum.Element e) {
        this._element = e;
    }

    public Enum.Field getField() {
        return this._field;
    }

    public void setField(Enum.Field newField) {
        this._field = newField;
    }

    public int getMistakeDay() {
        return this._mistakeDay;
    }

    public void setMistakeDay(int i) {
        this._mistakeDay = i;
    }

    public long getGrowthPeriod() {
        return this._growthPeriod;
    }

    public void setGrowthPeriod(long newGrowthPeriod) {
        this._growthPeriod = newGrowthPeriod < 0L ? 0L : newGrowthPeriod;
    }

    public Enum.Stage getGrowthStage() {
        return this._growthStage;
    }

    public void setGrowthStage(Enum.Stage newGrowthStage) {
        this._growthStage = newGrowthStage;
    }

    public byte getFullHealthPoints() {
        return this._fullHealthPoints;
    }

    public void setFullHealthPoints(byte newHealthPoints) {
        this._fullHealthPoints = newHealthPoints < 0 ? (byte)0 : (newHealthPoints > this.getMaxHealth() ? this.getMaxHealth() : newHealthPoints);
    }

    public byte getHealthPoints() {
        return this._healthPoints;
    }

    public void setHealthPoints(int h) {
        this._healthPoints = h <= 0 ? (byte)1 : (h > this._fullHealthPoints ? this._fullHealthPoints : (byte)h);
    }

    public byte getMaxHealth() {
        if (this._lapsedLife >= (long)Config._ultraHealthLifespanMin) {
            return Config._maxHealthUltra;
        }
        if (this._lapsedLife >= (long)Config._megaHealthLifespanMin) {
            return Config._maxHealthMega;
        }
        if (this._lapsedLife >= (long)Config._ultimateHealthLifespanMin) {
            return Config._maxHealthUltimate;
        }
        if (this._lapsedLife >= (long)Config._championHealthLifespanMin) {
            return Config._maxHealthChampion;
        }
        if (this._lapsedLife >= (long)Config._rookieHealthLifespanMin) {
            return Config._maxHealthRookie;
        }
        return Config._maxHealthDefault;
    }

    public boolean isFullyRecovered() {
        return this._healthPoints == this._fullHealthPoints;
    }

    public boolean isSick() {
        return this._sickLength > 0;
    }

    private void sicken() {
        if (!this.isSick()) {
            this._mistakeDay += Config._sickMistakeDayChange;
            this._world.setTravelSpeed((byte)0);
            Habitat h = this.getCurrentHabitat();
            int change = (this.compatibleElement(this._element, h) ? Config._compatibleElementSickLengthChange : (byte)0) + (this.compatibleField(this._field, h) ? Config._compatibleFieldSickLengthChange : (byte)0) + (this.incompatibleField(this._field, h) ? Config._incompatibleFieldSickLengthChange : (byte)0) + (this.incompatibleElement(this._element, h) ? Config._incompatibleElementSickLengthChange : (byte)0);
            this.setSickLength(Utility.randomBetween(Config._minSickLength, Config._sickLength + change));
            this.setMood(this._mood - Config._sickMoodDec);
            this.setEnthusiasm((byte)(this._enthusiasm + Config._sickEnthusiasmChange));
            this._timeRanks.decRankAndCheckFavDislikeChange(this.checkTime(this._clock.getHours()), Config._rankChangeSick);
            ++this._sickCount;
            this.setTotalLifespan(this._totalLifespan - (long)Config._sickLifeDec);
            if (Config._enableLifePenaltyAnim) {
                this.setStateNoRepeat(Enum.State.Bad_Health_Jeering);
            }
        }
    }

    public boolean isInj() {
        return this._injLength > 0;
    }

    private void injure(Enum.Attribute a, int rankChange) {
        if (!this.isInj()) {
            this._mistakeDay += Config._injuryMistakeDayChange;
            this._world.setTravelSpeed((byte)0);
            Habitat h = this.getCurrentHabitat();
            int change = (this.compatibleElement(this._element, h) ? Config._compatibleElementInjLengthChange : (byte)0) + (this.compatibleField(this._field, h) ? Config._compatibleFieldInjLengthChange : (byte)0) + (this.incompatibleField(this._field, h) ? Config._incompatibleFieldInjLengthChange : (byte)0) + (this.incompatibleElement(this._element, h) ? Config._incompatibleElementInjLengthChange : (byte)0);
            this.setInjLength(Utility.randomBetween(Config._minInjLength, Config._injLength + change));
            this.setMood(this._mood - Config._injuryMoodDec);
            this.setEnthusiasm((byte)(this._enthusiasm + Config._injuryEnthusiasmChange));
            this._timeRanks.decRankAndCheckFavDislikeChange(this.checkTime(this._clock.getHours()), Config._rankChangeInjury);
            ++this._injCount;
            this.setTotalLifespan(this._totalLifespan - (long)Config._injuryLifeDec);
            this.setEnergy((byte)(this._energy - Config._injuryEnergyDec));
            if (Config._enableLifePenaltyAnim) {
                this.setStateNoRepeat(Enum.State.Bad_Health_Jeering);
            }
            if (a != Enum.Attribute.None) {
                this._attributeRanks.decRankAndCheckFavDislikeChange(a, rankChange);
            }
        }
    }

    public int getSickCount() {
        return this._sickCount;
    }

    public int getInjCount() {
        return this._injCount;
    }

    public int getBattles() {
        return this._battles;
    }

    public void setBattles(int newBattles) {
        this._battles = newBattles < 0 ? 0 : newBattles;
    }

    public void setBits(int b) {
        if (b >= 0 && b <= Config._maxBits) {
            this._bits = b;
        }
    }

    public int getBits() {
        return this._bits;
    }

    public int getWins() {
        return this._wins;
    }

    public void setWins(int newWins) {
        if (newWins > 0) {
            this._wins = newWins;
        }
    }

    public int getPerfectWins() {
        return this._perfectWins;
    }

    public void checkAndIncPerfectWins(boolean forceInc) {
        if (forceInc || this._exercise >= Config._perfectWinsMinStrength && this._hunger >= Config._perfectWinsMinHunger && this._fullHealthPoints < this.getMaxHealth()) {
            ++this._perfectWins;
            if (this._perfectWins % Config._perfectWinsLimit == 0) {
                byte hp = this.getFullHealthPoints();
                this.setFullHealthPoints((byte)(this._fullHealthPoints + Config._perfectWinsHealthInc));
                if (hp < this.getFullHealthPoints()) {
                    this.setCurrentState(Enum.State.HealthInc);
                }
            } else {
                this.setCurrentState(Enum.State.PerfectWinsInc);
            }
        }
    }

    public int getLosses() {
        return this._battles - this._wins;
    }

    public String getWinRate() {
        if (this._battles > 0) {
            String rate = "" + (double)this._wins / (double)this._battles * 100.0;
            char[] resource = rate.toCharArray();
            rate = "";
            for (int i = 0; i < resource.length && resource[i] != '.'; ++i) {
                rate = rate + resource[i];
            }
            return rate;
        }
        return "0";
    }

    public Enum.XAntibodyState getXAntibodyState() {
        return this._xAntibodyState;
    }

    public boolean getAlive() {
        return this._alive;
    }

    public void setAlive(boolean newAlive) {
        if (this._alive && !newAlive) {
            switch (this._xAntibodyState) {
                case Temporary: 
                case Permanent: {
                    this._xAntibodyState = Enum.XAntibodyState.None;
                    this._xAntibodyCount = 0;
                    break;
                }
                case XProgram: {
                    this.setXAntibodyState(Enum.XAntibodyState.Permanent);
                }
            }
            this._currentState = Enum.State.Idling;
        }
        this._alive = newAlive;
    }

    public String getName() {
        return this._evolution.getDigimon(this._index).getName();
    }

    public int getIndex() {
        return this._index;
    }

    public void setIndex(int i) {
        this._index = i;
    }

    public int getItemInterestLapse() {
        return this._itemInterestLapse;
    }

    public void setItemInterestLapse(int lapse) {
        if (lapse <= 0) {
            this.setItemInterest((byte)(this._itemInterest - Config._itemInterestLapseDec));
            if (this._disposition > 0) {
                this._itemInterestLapse = Config._itemInterestLowTimer;
            } else if (this._disposition < 0) {
                this._itemInterestLapse = Config._itemInterestHighTimer;
            } else {
                this._itemInterest = Config._itemInterestTimer;
            }
        } else {
            this._itemInterestLapse = lapse > Config._itemInterestHighTimer ? Config._itemInterestHighTimer : (byte)lapse;
        }
    }

    public byte getVitaminLapse() {
        return this._vitaminLapse;
    }

    public void setVitaminLapse(byte newVitaminLapse) {
        this._vitaminLapse = newVitaminLapse < 0 ? (byte)0 : (newVitaminLapse > Config._vitaminHours ? Config._vitaminHours : newVitaminLapse);
    }

    public boolean hasVitamin() {
        return this._vitaminLapse > 0;
    }

    public void setVitamin(byte b) {
        this._vitamin = b > Config._maxVitamin ? Config._maxVitamin : (b < Config._minVitamin ? Config._minVitamin : b);
    }

    public void setMineral(byte b) {
        this._mineral = b > Config._maxMineral ? Config._maxMineral : (b < Config._minMineral ? Config._minMineral : b);
    }

    public void setProtein(byte b) {
        this._protein = b > Config._maxProtein ? Config._maxProtein : (b < Config._minProtein ? Config._minProtein : b);
    }

    public byte getBandageLapse() {
        return this._bandageLapse;
    }

    public void setBandageLapse(byte newBandageLapse) {
        this._bandageLapse = newBandageLapse < 0 ? (byte)0 : (newBandageLapse > Config._bandageHours ? Config._bandageHours : newBandageLapse);
    }

    public boolean getBandage() {
        return this._bandageLapse > 0;
    }

    public boolean getNap() {
        return this._nap;
    }

    public void setNap(boolean newNap) {
        this._nap = newNap;
        this.setAsleep(this._nap);
    }

    public byte getMedLapse() {
        return this._medLapse;
    }

    public void setMedLapse(byte newMedLapse) {
        this._medLapse = newMedLapse < 0 ? (byte)0 : (newMedLapse > Config._medicineHours ? Config._medicineHours : newMedLapse);
    }

    public boolean getMed() {
        return this._medLapse > 0;
    }

    public void setSickLength(int s) {
        if (this._sickLength > s && this.getGoodNutrition() && s + Config._goodNutritionSickLapseChange < this._sickLength) {
            s += Config._goodNutritionSickLapseChange;
        }
        this._sickLength = s <= 0 ? (byte)0 : (s > Config._sickLength ? Config._sickLength : (byte)s);
    }

    public void setInjLength(int i) {
        if (this._injLength > i && this.getGoodNutrition() && i + Config._goodNutritionInjLapseChange < this._injLength) {
            i += Config._goodNutritionInjLapseChange;
        }
        this._injLength = i <= 0 ? (byte)0 : (i > Config._injLength ? Config._injLength : (byte)i);
    }

    public boolean isFatigued() {
        return this._fatigueLength > 0;
    }

    public void setFatigueLength(int f) {
        if (this._fatigueLength > f && this.getGoodNutrition() && f + Config._goodNutritionFatigueLapseChange < this._fatigueLength) {
            f += Config._goodNutritionFatigueLapseChange;
        }
        if (f <= 0) {
            if (this._fatigueLength > 0 && this._exercise > Config._fullStrength) {
                this._exercise = Config._fullStrength;
            }
            this._fatigueLength = 0;
        } else {
            this._fatigueLength = f > Config._fatigueMax ? Config._fatigueMax : (byte)f;
        }
    }

    public int getSleepLapse() {
        return this._sleepLapse;
    }

    public void setSleepLapse(int newSleepLapse) {
        this._sleepLapse = newSleepLapse < 0 ? 0 : newSleepLapse;
        if (this._sleepLapse >= this._sleepLimit) {
            this.sleep();
        }
    }

    private int getEffectEnergyGain() {
        int i = 0;
        for (CareEffect c : this._careEffects) {
            if (!c.isActive()) continue;
            i += c.getEnergyChange()[0] * (c.getEnergyChange()[1] / 60);
        }
        return i;
    }

    private void sleep() {
        this._sleepLapse = 0;
        this.setAsleep(true);
        this._awakeLimit = (int)Math.ceil((double)(this._maxEnergy - this._energy) / (double)(this._energyGain + this.getEffectEnergyGain())) * this._sleepMinutesToEnergyGain;
        if (this._awakeLimit > Config._maxAwakeLimit) {
            this._awakeLimit = Config._maxAwakeLimit;
        } else if (this._awakeLimit < Config._minAwakeLimit) {
            this._awakeLimit = Config._minAwakeLimit;
        }
        this._sleepLimit = Config._hoursDay * Config._minutesHour - this._awakeLimit;
    }

    public int getSleepLimit() {
        return this._sleepLimit;
    }

    private void incSleepMinutes(int energyGain) {
        this._sleepMinutes += this._awakeLapseInc;
        if (this._sleepMinutes >= this._sleepMinutesToEnergyGain) {
            this._sleepMinutes -= this._sleepMinutesToEnergyGain;
            this.setEnergy((byte)(this._energy + energyGain));
        }
    }

    public int getAwakeLapse() {
        return this._awakeLapse;
    }

    public void setAwakeLapse(int newAwakeLapse) {
        if (newAwakeLapse != this._awakeLapse) {
            Random ran = new Random();
            int r = ran.nextInt(Config._moreSleepChance) + this._restless * Config._awakeLapseRestlessCoefficient;
            if (r < 0) {
                --newAwakeLapse;
            } else if (r > Config._moreSleepChance - 1) {
                ++newAwakeLapse;
                if (this._nap) {
                    this.checkNapEnergy(Config._napEnergyMin);
                } else {
                    this.incSleepMinutes(Config._bonusSleepEnergy);
                }
            }
            this._awakeLapse = newAwakeLapse < 0 ? 0 : newAwakeLapse;
            if (this._awakeLapse >= this._awakeLimit) {
                this.setAsleep(false);
                this._awakeLapse = 0;
                this._sleepLimit = Config._hoursDay * Config._minutesHour - this._awakeLimit;
                if (!this._lights) {
                    this.setLights(true);
                }
            }
        }
    }

    public int getAwakeLimit() {
        return this._awakeLimit;
    }

    public boolean getDisciplineCall() {
        return this._disciplineCall;
    }

    public void setDisciplineCall(boolean newDiscipline) {
        if (this._disciplineCall && !newDiscipline) {
            this.setObedience(this._obedience - Config._disciplineCallObedienceDec);
            this.setMood(this._mood + Config._disciplineCallMoodInc);
            this.setScoldWindow((byte)0);
            this._callMinutesDiscipline = 0;
            this.autoSave();
        }
        this._disciplineCall = newDiscipline;
    }

    public WorldMap getWorld() {
        return this._world;
    }

    public void setEvolHistory(ArrayList<int[]> newHistory) {
        this._evolHistory = newHistory;
    }

    public ArrayList<int[]> getEvolHistory() {
        return this._evolHistory;
    }

    public ArrayList<ArrayList<int[]>> getGenerationHistory() {
        ArrayList<ArrayList<int[]>> a = new ArrayList<ArrayList<int[]>>();
        a.addAll(this._generationHistory);
        a.add(this.createGenerationRecord());
        return a;
    }

    private void loadCurrentHabitat() {
        this._currentHabitat = this._homeHabitat;
        WeatherRecord w = this.getExistingWeatherRecord(null, null);
        if (w != null) {
            this.setCurrentWeatherFromRecord(w);
        }
    }

    public void setCurrentHabitat(int habitat) {
        this.setCurrentHabitat(habitat, true);
    }

    public void setCurrentHabitat(int habitat, boolean randomWeather) {
        if (habitat >= 0 && habitat < this._habitats.size()) {
            MapLevel map = this._world.getCurrentMap();
            Zone zone = this._world.getCurrentZone();
            if (this._isHome) {
                this._homeHabitat = habitat;
            }
            this._currentHabitat = habitat;
            Enum.Weather old = this._currentWeather;
            this._currentWeather = Enum.Weather.Clear;
            WeatherRecord w = this.getExistingWeatherRecord(map, zone);
            if (w == null) {
                if (randomWeather) {
                    this.randomWeather(habitat);
                } else {
                    this.transitionWeather(old);
                }
                this.addCurrentWeatherToRecord(w, map, zone);
            } else {
                this.setCurrentWeatherFromRecord(w);
            }
        }
    }

    public Habitat getCurrentHabitat() {
        return this._habitats.get(this._currentHabitat);
    }

    public int getCurrentHabitatIndex() {
        return this._currentHabitat;
    }

    public ArrayList<Habitat> getHabitats() {
        return this._habitats;
    }

    public ArrayList<Habitat> getOwnedHabitats() {
        ArrayList<Habitat> habitats = new ArrayList<Habitat>();
        for (Habitat h : this._habitats) {
            if (!h.getUnlocked()) continue;
            habitats.add(h);
        }
        return habitats;
    }

    public int getHabitatIndex(Habitat habitat) {
        int index = 0;
        for (int i = 0; i < this._habitats.size(); ++i) {
            if (!this._habitats.get(i).getFileName().equals(habitat.getFileName())) continue;
            index = i;
            break;
        }
        return index;
    }

    public int getHabitatShopSize() {
        int i = 0;
        for (Habitat h : this._habitats) {
            if (h.getPrice() <= 0) continue;
            ++i;
        }
        return i;
    }

    public ArrayList<Habitat> getShopHabitats() {
        ArrayList<Habitat> a = new ArrayList<Habitat>();
        for (Habitat h : this._habitats) {
            if (h.getPrice() <= 0 || h.getUnlocked()) continue;
            a.add(h);
        }
        return a;
    }

    public boolean lockedHabitatsRemain() {
        for (Habitat h : this._habitats) {
            if (h.getUnlocked() || h.getPrice() <= 0) continue;
            return true;
        }
        return false;
    }

    public boolean getIsHome() {
        return this._isHome;
    }

    public void setIsHome(boolean h) {
        this._isHome = h;
        if (!this._isHome) {
            Zone zone = this._world.getCurrentZone();
            if (zone != null) {
                this.setCurrentHabitat(zone.getCurrentLocationBackground());
            }
        } else {
            this.setCurrentHabitat(this._homeHabitat);
        }
        this._world.setTravelSpeed((byte)0);
    }

    public void setBattleImmunity(boolean i) {
        this._battleImmunity = i ? this.scaleToClock(Config._battleImmunitySeconds) : 0;
    }

    public boolean getBattleImmunity() {
        return this._battleImmunity != 0;
    }

    public boolean getAmenitiesOpen() {
        return this._isHome || this._world.getCurrentZone() != null && this._world.getCurrentZone().isTown() != null;
    }

    public byte[] getFoodShopTime() {
        if (this._isHome) {
            return Config._foodShopTime.get(this.getSeason().ordinal());
        }
        Town t = this._world.getCurrentZone().isTown();
        if (t != null) {
            return t.getFoodShopTime().get(this.getSeason().ordinal());
        }
        return null;
    }

    public byte[] getItemShopTime() {
        if (this._isHome) {
            return Config._itemShopTime.get(this.getSeason().ordinal());
        }
        Town t = this._world.getCurrentZone().isTown();
        if (t != null) {
            return t.getItemShopTime().get(this.getSeason().ordinal());
        }
        return null;
    }

    public byte[] getHabitatShopTime() {
        if (this._isHome) {
            return Config._habitatShopTime.get(this.getSeason().ordinal());
        }
        Town t = this._world.getCurrentZone().isTown();
        if (t != null) {
            return t.getHabitatShopTime().get(this.getSeason().ordinal());
        }
        return null;
    }

    public boolean isShopOpen(byte[] time) {
        if (time != null) {
            return Utility.isOpen(this._clock.getHours(), time);
        }
        return false;
    }

    public int[] getGift() {
        return this._gift;
    }

    public void setGift(int[] s) {
        this._gift = s;
    }

    public String getRequestMessage() {
        String m = this._requestMessage;
        return m;
    }

    public Affinity getAffinity() {
        return this._affinity;
    }

    public int getMeatEaten() {
        return this._meatEaten;
    }

    public int getVegEaten() {
        return this._vegEaten;
    }

    public int getFruitEaten() {
        return this._fruitEaten;
    }

    public int getFishEaten() {
        return this._fishEaten;
    }

    public int getJunkEaten() {
        return this._junkEaten;
    }

    public int getMedEaten() {
        return this._medEaten;
    }

    public ArrayList<Integer> getUniqueLevelFought() {
        ArrayList<Integer> levels = new ArrayList<Integer>();
        for (Integer i : this._levelsFought) {
            if (levels.contains(i)) continue;
            levels.add(i);
        }
        return levels;
    }

    public boolean levelsFoughtIsEmpty() {
        return this._levelsFought.size() == 0;
    }

    public int getLevelFought(int level) {
        int count = 0;
        for (int i : this._levelsFought) {
            if (i < level) continue;
            ++count;
        }
        return count;
    }

    public int getLevelCount(int level) {
        int count = 0;
        for (int i : this._levelsFought) {
            if (i != level) continue;
            ++count;
        }
        return count;
    }

    public void addLevelFought(int level) {
        this._levelsFought.add(level);
    }

    public void setCanEvolveOrDie(boolean b) {
        this._canEvolveOrDie = b;
    }

    public boolean getPostponeEvolve() {
        return this._postponeEvolve;
    }

    public boolean getPostponeDie() {
        return this._postponeDie;
    }

    public void setSettings(ViewSettings settings) {
        this._settings = settings;
    }

    public int[] getHabitatRecord() {
        return this._habitatRecord;
    }

    public int getMajorHabitat() {
        return this.getMajority(this._habitatRecord);
    }

    public int[] getMoodRecord() {
        return this._moodRecord;
    }

    public Enum.Mood getMajorMood(int[] mood) {
        Enum.Mood m = Enum.Mood.None;
        int index = this.getMajority(mood);
        if (index != -1) {
            m = Enum.Mood.values()[index];
        }
        return m;
    }

    public Enum.Mood getDailyMood() {
        return this.getMajorMood(this._dailyMoodRecord);
    }

    public int[] getWeightHabitat() {
        return this._weightRecord;
    }

    public Enum.Weight getMajorWeight() {
        Enum.Weight m = Enum.Weight.None;
        int index = this.getMajority(this._weightRecord);
        if (index != -1) {
            m = Enum.Weight.values()[index];
        }
        return m;
    }

    public byte getProtein() {
        return this._protein;
    }

    public byte getMineral() {
        return this._mineral;
    }

    public byte getVitamin() {
        return this._vitamin;
    }

    public boolean getGoodNutrition() {
        return this._mineral >= Config._goodNutritionMin && this._protein >= Config._goodNutritionMin && this._vitamin >= Config._goodNutritionMin;
    }

    public void setUnlockConsumable(int i) {
        this._unlockConsumable = i;
    }

    public int getUnlockConsumable() {
        return this._unlockConsumable;
    }

    public PhysicalState(String modFolder, String modelFolder, boolean tournament) {
        this._tournamentVersion = tournament;
        this.MOD_FOLDER = modFolder;
        this.MODEL_FOLDER = modelFolder;
        this._evolution = new Evolution(this.getModFolder(), this.MODEL_FOLDER);
        this._affinity = this.buildAffinity();
        this._foodTypes = this.buildFoodTypes();
        this._items = this.buildItems();
        this._habitats = this.buildHabitats();
        this._habitatRecord = new int[this._habitats.size()];
        this._careEffects = this.buildLifeEffects();
        this._tournament = new Tournament(this, this.getModFolder(), this.MODEL_FOLDER);
    }

    private void defaultData() {
        this._evolHistory.clear();
        this._currentState = Enum.State.Idling;
        this._savedFromDeath = 0;
        this._postponeDie = false;
        this._postponeEvolve = false;
        this._index = 0;
        this._age = 0;
        this._sickCount = 0;
        this._injCount = 0;
        this._mistakeDay = 0;
        this._timeToAge = 0;
        this._totalLifespan = 0L;
        this._lapsedLife = 0L;
        this._growthPeriod = 0L;
        this._growthStage = Enum.Stage.Egg;
        this._baseWeight = 5;
        this._stomachCapacity = (byte)10;
        this._healthPoints = this._fullHealthPoints = Config._startingHealthPoints;
        this._battles = 0;
        this._wins = 0;
        this._perfectWins = 0;
        this._vaccinePower = 0;
        this._dataPower = 0;
        this._virusPower = 0;
        this._toiletTrained = 0;
        this._currentMood = Enum.Mood.Neutral;
        this._mood = 0;
        this._obedience = 0;
        this._glutton = 0;
        this._restless = 0;
        this._disposition = 0;
        this.randPersonalityTraits();
        this._attribute = Enum.Attribute.None;
        this._field = Enum.Field.None;
        this._element = Enum.Element.None;
        this._foodRanks.resetRanks();
        this._attributeRanks.resetRanks();
        this._timeRanks.resetRanks();
        this._foodRanks.setFavorite(this.calcFavFood());
        this._attributeRanks.setFavorite(this.calcFavAtt());
        this._timeRanks.setFavorite(this.calcFavTime());
        this._foodRanks.setUnlockedFav(false);
        this._attributeRanks.setUnlockedFav(false);
        this._timeRanks.setUnlockedFav(false);
        this._foodRanks.setDisliked(this.calcDislikedFood());
        this._attributeRanks.setDisliked(this.calcDislikedAtt());
        this._timeRanks.setDisliked(this.calcDislikedTime());
        this._foodRanks.setUnlockedDislike(this._foodRanks.getDisliked() == Enum.Food.None);
        this._attributeRanks.setUnlockedDislike(this._attributeRanks.getDisliked() == Enum.Attribute.None);
        this._timeRanks.setUnlockedDislike(this._timeRanks.getDisliked() == Enum.Time.None);
        this._isHome = true;
        this.resetToEgg();
        this.xAntibodyChance();
        this._animQueue.clear();
    }

    private void xAntibodyChance() {
        if (Utility.randomChance(Config._xAntibodyBirthChanceTarget, Config._xAntibodyBirthChanceBound)) {
            this.setXAntibodyState(Enum.XAntibodyState.Permanent);
        }
    }

    private ArrayList<int[]> createGenerationRecord() {
        ArrayList<int[]> a = new ArrayList<int[]>();
        a.add(new int[]{this._index, -1});
        a.add(new int[]{this._age, -1});
        for (int[] i : this._evolHistory) {
            a.add(i);
        }
        return a;
    }

    public void resetDigimon(boolean recordGeneration) {
        if (recordGeneration) {
            this._generationHistory.add(this.createGenerationRecord());
        }
        this.careBonusOnReset();
        this._strengthDecayLapse = this._hungerDecayLapse = this._clock.getMinutes();
        this.defaultData();
        Zone z = this._world.getCurrentZone();
        this._world.setAdventureLife(Config._maxAdventureLife);
        if (z != null) {
            this._world.changeZone(z.getIsComplete(), this._world.getCurrentMap().getZones().get(0), false);
        }
        if ((z = this._world.getCurrentZone()) != null) {
            z.setCurrentLocation(0);
        }
        this.autoSave();
    }

    public void resetToEgg() {
        this._alive = true;
        this._hunger = Config._fullHunger;
        this._bmGauge = 0;
        this._calories = Config._startingCalories;
        this._weight = this._baseWeight;
        this._overweight = Enum.Weight.Healthy;
        this._exercise = Config._fullStrength;
        this._exerciseLimit = Config._fullStrength;
        this._energy = this._maxEnergy;
        this._enthusiasm = 0;
        this._refused = false;
        this._compliance = false;
        this._praise = false;
        this._scold = false;
        this._praiseWindow = 0;
        this._scoldWindow = 0;
        this._asleep = false;
        this.setLights(true);
        this._autoCare = false;
        this._mistake = 0;
        this._overeat = 0;
        this._disturb = 0;
        this.resetAllCallMinutes();
        this._sleepLimit = 960;
        this._sleepLapse = 0;
        this._awakeLimit = 480;
        this._awakeLapse = 0;
        this._dayTrain = 0;
        this._morningTrain = 0;
        this._nightTrain = 0;
        this._asleep = false;
        this._vitaminLapse = 0;
        this._bandageLapse = 0;
        this._nap = false;
        this._toNapSleepLapse = 0;
        this._medLapse = 0;
        this._sickLength = 0;
        this._injLength = 0;
        this._fatigueLength = 0;
        this._meatEaten = 0;
        this._vegEaten = 0;
        this._fruitEaten = 0;
        this._fishEaten = 0;
        this._junkEaten = 0;
        this._medEaten = 0;
        this._grainEaten = 0;
        this._dairyEaten = 0;
        this._battleImmunity = 0;
        this._dna.resetDNA();
        this._levelsFought.clear();
        this.resetRecords();
        this._temp = (byte)((this._idealTemp[0] + this._idealTemp[1]) / 2);
        this.calcHungerDecayLapse();
        this.calcStrengthDecayLapse();
    }

    private void careBonusOnReset() {
        boolean isFailed = this.isFilthyEvol();
        this._bonus = this._mistake > 0 ? (this._bonus -= this._mistake) : ++this._bonus;
        if (this._currentMood == Enum.Mood.Happy) {
            ++this._bonus;
        } else if (this._currentMood != Enum.Mood.Neutral) {
            --this._bonus;
        }
        if (this._obedience > Config._bonusIncObedience) {
            ++this._bonus;
        } else if (this._obedience < Config._bonusDecObedience) {
            --this._bonus;
        }
        if (Integer.parseInt(this.getWinRate()) >= Config._bonusIncWinRate) {
            ++this._bonus;
        }
        this._bonus = (int)((long)this._bonus + (this._lapsedLife - this._growthPeriod) / 60L / 60L / 24L);
        switch (this._growthStage) {
            case Champion: {
                if (!isFailed) {
                    ++this._bonus;
                }
                if (this._vaccinePower + this._dataPower + this._virusPower >= Config._bonusIncChampionAttribute) {
                    ++this._bonus;
                }
                if (this._battles <= Config._bonusIncChampionBattles) break;
                ++this._bonus;
                break;
            }
            case Ultimate: {
                this._bonus += Config._bonusIncUltimate;
                if (this._vaccinePower + this._dataPower + this._virusPower >= Config._bonusIncUltimateAttribute) {
                    ++this._bonus;
                }
                if (this._battles <= Config._bonusIncUltimateBattles) break;
                ++this._bonus;
                break;
            }
            case Mega: {
                this._bonus += Config._bonusIncMega;
                if (this._vaccinePower + this._dataPower + this._virusPower >= Config._bonusIncMegaAttribute) {
                    ++this._bonus;
                }
                if (this._battles <= Config._bonusIncMegaBattles) break;
                ++this._bonus;
            }
        }
        if (this._bonus < 0) {
            this._bonus = 0;
        }
    }

    public void setNewDigimemory() {
        String desc;
        Item digimemory = this.getDigimemory();
        digimemory._data = 0;
        digimemory._vaccine = 0;
        digimemory._virus = 0;
        digimemory._seconds = 0;
        digimemory._description = desc = "Empty inheritance data";
        digimemory._details = "";
        digimemory.remove();
        if (this._bonus > 0) {
            int vaccine = (int)Math.floor((double)this._vaccinePower * ((double)this._bonus * Config._digimemoryAttributeCoefficient));
            int data = (int)Math.floor((double)this._dataPower * ((double)this._bonus * Config._digimemoryAttributeCoefficient));
            int virus = (int)Math.floor((double)this._virusPower * ((double)this._bonus * Config._digimemoryAttributeCoefficient));
            int lifeInc = Config._digimemoryLifeIncCoefficient * this._bonus;
            digimemory._data = data;
            digimemory._vaccine = vaccine;
            digimemory._virus = virus;
            digimemory._seconds = lifeInc;
            digimemory._description = desc = "Inheritance data:<br>" + this.getName() + "<br>Va+" + vaccine + " | D+" + data + " | Vi+" + virus;
            digimemory._details = "" + this.getIndex();
            digimemory.incQuantity();
        }
        this._bonus = 0;
    }

    private void randPersonalityTraits() {
        int r;
        Random ran = new Random();
        if (Config._calorieModUpperLimit > 0) {
            this._calorieMaxMod = ran.nextInt(Config._calorieModUpperLimit);
            this._calorieMinMod = ran.nextInt(Config._calorieModUpperLimit);
        }
        if ((r = ran.nextInt(3)) < 1) {
            this._restless = (byte)-1;
            this._energyRank = Config._personalityChampRandomLowEnergyRank;
        } else if (r > 1) {
            this._restless = 1;
            this._energyRank = Config._personalityChampRandomHighEnergyRank;
        } else if (r == 1) {
            this._restless = 0;
            this._energyRank = 0;
        }
        ran = new Random();
        r = ran.nextInt(3);
        if (r < 1 && this._glutton == 0) {
            this._glutton = (byte)-1;
            this._weightRank = Config._personalityChampRandomLowWeightRank;
        } else if (r > 1 && this._glutton == 0) {
            this._glutton = 1;
            this._weightRank = Config._personalityChampRandomHighWeightRank;
        } else if (r == 1) {
            this._glutton = 0;
            this._weightRank = 0;
        }
        ran = new Random();
        r = ran.nextInt(3);
        if (r < 1 && this._disposition == 0) {
            this._disposition = (byte)-1;
            this._moodRank = Config._personalityChampRandomLowMoodRank;
        } else if (r > 1 && this._disposition == 0) {
            this._disposition = 1;
            this._moodRank = Config._personalityChampRandomHighMoodRank;
        } else if (r == 1) {
            this._disposition = 0;
            this._moodRank = 0;
        }
        this._personality = this.checkPersonality();
    }

    private void changePersonality(Enum.Personality p) {
        this._personality = p;
        switch (p) {
            case Docile: {
                this._disposition = 0;
                this._glutton = 0;
                this._restless = 0;
                break;
            }
            case Gluttonous: {
                this._disposition = 0;
                this._glutton = 1;
                this._restless = 0;
                break;
            }
            case Restless: {
                this._disposition = 0;
                this._glutton = 0;
                this._restless = 1;
                break;
            }
            case Content: {
                this._disposition = 0;
                this._glutton = (byte)-1;
                this._restless = 0;
                break;
            }
            case Calm: {
                this._disposition = 0;
                this._glutton = 0;
                this._restless = (byte)-1;
                break;
            }
            case Hasty: {
                this._disposition = 0;
                this._glutton = 1;
                this._restless = 1;
                break;
            }
            case Lazy: {
                this._disposition = 0;
                this._glutton = 1;
                this._restless = (byte)-1;
                break;
            }
            case Fidgety: {
                this._disposition = 0;
                this._glutton = (byte)-1;
                this._restless = 1;
                break;
            }
            case Stoic: {
                this._disposition = 0;
                this._glutton = (byte)-1;
                this._restless = (byte)-1;
                break;
            }
            case Cheerful: {
                this._disposition = 1;
                this._glutton = 0;
                this._restless = 0;
                break;
            }
            case Eager: {
                this._disposition = 1;
                this._glutton = 1;
                this._restless = 0;
                break;
            }
            case Hyper: {
                this._disposition = 1;
                this._glutton = 0;
                this._restless = 1;
                break;
            }
            case Generous: {
                this._disposition = 1;
                this._glutton = (byte)-1;
                this._restless = 0;
                break;
            }
            case Carefree: {
                this._disposition = 1;
                this._glutton = 0;
                this._restless = (byte)-1;
                break;
            }
            case Playful: {
                this._disposition = 1;
                this._glutton = 1;
                this._restless = 1;
                break;
            }
            case Loafing: {
                this._disposition = 1;
                this._glutton = 1;
                this._restless = (byte)-1;
                break;
            }
            case Antsy: {
                this._disposition = 1;
                this._glutton = (byte)-1;
                this._restless = 1;
                break;
            }
            case Mellow: {
                this._disposition = 1;
                this._glutton = (byte)-1;
                this._restless = (byte)-1;
                break;
            }
            case Serious: {
                this._disposition = (byte)-1;
                this._glutton = 0;
                this._restless = 0;
                break;
            }
            case Selfish: {
                this._disposition = (byte)-1;
                this._glutton = 1;
                this._restless = 0;
                break;
            }
            case Anxious: {
                this._disposition = (byte)-1;
                this._glutton = 0;
                this._restless = 1;
                break;
            }
            case Tolerant: {
                this._disposition = (byte)-1;
                this._glutton = (byte)-1;
                this._restless = 0;
                break;
            }
            case Apathetic: {
                this._disposition = (byte)-1;
                this._glutton = 0;
                this._restless = (byte)-1;
                break;
            }
            case Impish: {
                this._disposition = (byte)-1;
                this._glutton = 1;
                this._restless = 1;
                break;
            }
            case Lethargic: {
                this._disposition = (byte)-1;
                this._glutton = 1;
                this._restless = (byte)-1;
                break;
            }
            case Unruly: {
                this._disposition = (byte)-1;
                this._glutton = (byte)-1;
                this._restless = 1;
                break;
            }
            case Callous: {
                this._disposition = (byte)-1;
                this._glutton = (byte)-1;
                this._restless = (byte)-1;
                break;
            }
        }
    }

    private Enum.Personality checkPersonality() {
        Enum.Personality p = null;
        p = this._disposition == 0 ? (this._glutton == 0 ? (this._restless == 0 ? Enum.Personality.Docile : (this._restless == 1 ? Enum.Personality.Restless : Enum.Personality.Calm)) : (this._glutton == 1 ? (this._restless == 0 ? Enum.Personality.Gluttonous : (this._restless == 1 ? Enum.Personality.Hasty : Enum.Personality.Lazy)) : (this._restless == 0 ? Enum.Personality.Content : (this._restless == 1 ? Enum.Personality.Fidgety : Enum.Personality.Stoic)))) : (this._disposition == 1 ? (this._glutton == 0 ? (this._restless == 0 ? Enum.Personality.Cheerful : (this._restless == 1 ? Enum.Personality.Hyper : Enum.Personality.Carefree)) : (this._glutton == 1 ? (this._restless == 0 ? Enum.Personality.Eager : (this._restless == 1 ? Enum.Personality.Playful : Enum.Personality.Loafing)) : (this._restless == 0 ? Enum.Personality.Generous : (this._restless == 1 ? Enum.Personality.Antsy : Enum.Personality.Mellow)))) : (this._glutton == 0 ? (this._restless == 0 ? Enum.Personality.Serious : (this._restless == 1 ? Enum.Personality.Anxious : Enum.Personality.Apathetic)) : (this._glutton == 1 ? (this._restless == 0 ? Enum.Personality.Selfish : (this._restless == 1 ? Enum.Personality.Impish : Enum.Personality.Lethargic)) : (this._restless == 0 ? Enum.Personality.Tolerant : (this._restless == 1 ? Enum.Personality.Unruly : Enum.Personality.Callous)))));
        return p;
    }

    public void randOnChampion() {
        this._restless = this._energyRank >= Config._personalityChampRandomHighEnergyRank ? (byte)1 : (this._energyRank <= Config._personalityChampRandomLowEnergyRank ? (byte)-1 : (byte)0);
        this._glutton = this._weightRank >= Config._personalityChampRandomHighWeightRank ? (byte)1 : (this._weightRank <= Config._personalityChampRandomLowWeightRank ? (byte)-1 : (byte)0);
        this._disposition = this._moodRank >= Config._personalityChampRandomHighMoodRank ? (byte)1 : (this._moodRank <= Config._personalityChampRandomLowMoodRank ? (byte)-1 : (byte)0);
        this._personality = this.checkPersonality();
    }

    public void personalityTracker(byte currentMin) {
        if (this._growthStage != Enum.Stage.Egg && currentMin % Config._personalityTrackLapseMin == 0 && (this._growthStage == Enum.Stage.Fresh || this._growthStage == Enum.Stage.InTraining || this._growthStage == Enum.Stage.Rookie)) {
            if ((double)this._energy >= Config._personalityChampRandomHighEnergy * (double)this._maxEnergy) {
                ++this._energyRank;
            } else if ((double)this._energy <= Config._personalityChampRandomLowEnergy * (double)this._maxEnergy) {
                --this._energyRank;
            }
            if (this._overweight == Enum.Weight.Over) {
                ++this._weightRank;
            } else if (this._overweight == Enum.Weight.Under) {
                --this._weightRank;
            }
            if (this._currentMood == Enum.Mood.Happy) {
                ++this._moodRank;
            } else if (this._currentMood == Enum.Mood.Unhappy || this._currentMood == Enum.Mood.Depressed) {
                --this._moodRank;
            }
        }
    }

    public void changeMoodRank(int change) {
        this._moodRank += change;
    }

    private Enum.Food calcFavFood() {
        Random ran = new Random();
        int r = ran.nextInt(Config._validLikedFood.size());
        Enum.Food f = Config._validLikedFood.get(r);
        this._foodRanks.getRank(f).setRank(Config._rankLimit);
        return f;
    }

    private Enum.Food calcDislikedFood() {
        ArrayList<Enum.Food> list = new ArrayList<Enum.Food>(Config._validDislikedFood);
        list.remove((Object)this._foodRanks.getFavorite());
        Random ran = new Random();
        int r = ran.nextInt(list.size());
        Enum.Food f = list.get(r);
        this._foodRanks.getRank(f).setRank(Config._rankMinimum);
        return f;
    }

    private void incFoodRankAndEaten(ArrayList<Enum.Food> food) {
        for (Enum.Food f : food) {
            if (f == Enum.Food.None) continue;
            switch (f) {
                case Meat: {
                    ++this._meatEaten;
                    break;
                }
                case Fruit: {
                    ++this._fruitEaten;
                    break;
                }
                case Veg: {
                    ++this._vegEaten;
                    break;
                }
                case Fish: {
                    ++this._fishEaten;
                    break;
                }
                case Med: {
                    ++this._medEaten;
                    break;
                }
                case Junk: {
                    ++this._junkEaten;
                    break;
                }
                case Dairy: {
                    ++this._dairyEaten;
                    break;
                }
                case Grain: {
                    ++this._grainEaten;
                }
            }
            this._foodRanks.changeRank(f);
        }
    }

    private Enum.Attribute calcFavAtt() {
        Random ran = new Random();
        int r = ran.nextInt(Config._validLikedAttribute.size());
        Enum.Attribute a = Config._validLikedAttribute.get(r);
        this._attributeRanks.getRank(a).setRank(Config._rankLimit);
        return a;
    }

    private Enum.Attribute calcDislikedAtt() {
        ArrayList<Enum.Attribute> list = new ArrayList<Enum.Attribute>(Config._validDislikedAttribute);
        list.remove((Object)this._attributeRanks.getFavorite());
        Random ran = new Random();
        int r = ran.nextInt(list.size());
        Enum.Attribute a = list.get(r);
        this._attributeRanks.getRank(a).setRank(Config._rankMinimum);
        return a;
    }

    public void incAttRank(Enum.Attribute att) {
        if (att != Enum.Attribute.None) {
            this._attributeRanks.changeRank(att);
        } else {
            this.changeMoodRank(Config._noneTrainingAttributeMoodRankChange);
        }
    }

    private Enum.Time calcFavTime() {
        Random ran = new Random();
        int r = ran.nextInt(Config._validLikedTime.size());
        Enum.Time t = Config._validLikedTime.get(r);
        this._timeRanks.getRank(t).setRank(Config._rankLimit);
        return t;
    }

    private Enum.Time calcDislikedTime() {
        ArrayList<Enum.Time> list = new ArrayList<Enum.Time>(Config._validDislikedTime);
        list.remove((Object)this._timeRanks.getFavorite());
        Random ran = new Random();
        int r = ran.nextInt(list.size());
        Enum.Time t = list.get(r);
        this._timeRanks.getRank(t).setRank(Config._rankMinimum);
        return t;
    }

    public void assistantFeed(FoodType foodType) {
        this.feed(foodType, false, Enum.State.Assistant_Feed);
    }

    public boolean feed(FoodType foodType) {
        return this.feed(foodType, Config._canRefuse, Enum.State.Eating);
    }

    private boolean feed(FoodType foodType, boolean canRefuse, Enum.State state) {
        boolean complied = false;
        if ((state == Enum.State.Assistant_Feed || state != Enum.State.Assistant_Feed && this._currentState != Enum.State.Assistant_Feed && !this._animQueue.contains((Object)Enum.State.Assistant_Feed)) && this._growthStage != Enum.Stage.Egg) {
            if (foodType.disturb()) {
                this.disturb(foodType);
            }
            if (this.checkMaxHoursBeforeSleep(foodType)) {
                this.checkRefused(foodType, null, false, 0.0, canRefuse);
                complied = this.checkCompliant();
                if (!this._refused) {
                    byte mod;
                    this.setDisciplineCall(false);
                    byte by = this._glutton == 1 ? Config._gluttonFeedMoodChange : (mod = this._glutton == -1 ? Config._notGluttonFeedMoodChange : (byte)0);
                    if (foodType.getType().contains((Object)this._foodRanks.getDisliked())) {
                        this._foodRanks.setUnlockedDislike(true);
                        if (this._hunger >= Config._fullHunger) {
                            this.setMood(this._mood - Config._favFoodMoodInc + mod);
                            this.setEnthusiasm((byte)(this._enthusiasm - Config._favFoodEnthusiasmInc + (complied ? Config._enthusiasmChangeBadFoodForced : (byte)0)));
                        }
                        this.setMood(this._mood - Config._favFoodMoodInc + mod);
                        this.setObedience(this._obedience + Config._dislikedFoodObedienceChange);
                    } else if (foodType.getType().contains((Object)this._foodRanks.getFavorite())) {
                        this._foodRanks.setUnlockedFav(true);
                        if (this._hunger < Config._fullHunger || this._glutton == 1 && this._hunger < this.getOvereatLimit(this.getStomachCapacity())) {
                            this.setMood(this._mood + Config._favFoodMoodInc + mod);
                            this.setEnthusiasm((byte)(this._enthusiasm + Config._favFoodEnthusiasmInc));
                        } else if (this._hunger < this.getStomachCapacity()) {
                            this.setMood(this._mood + Config._foodMoodInc + mod);
                        }
                    } else if (this._hunger < this.getStomachCapacity()) {
                        this.setMood(this._mood + Config._foodMoodInc + mod);
                    }
                    this.applyFood(foodType, complied, state);
                    this.incFoodRankAndEaten(foodType.getType());
                    foodType.decQuantity();
                    this.checkDirtyEating(foodType.getType(), complied);
                    this.checkIntolerantFoodSick(foodType.getType(), complied);
                } else {
                    this.setStateNoRepeat(Enum.State.Refusing);
                }
            } else {
                this.setStateNoRepeat(Enum.State.Jeering);
            }
            this.autoSave();
        }
        return complied;
    }

    private void checkIntolerantFoodSick(ArrayList<Enum.Food> f, boolean complied) {
        if (this.isIntolerant(f)) {
            boolean worse = this.checkWorseSick(Config._intolerantFoodWorseSickChance);
            boolean sick = this.checkSick(Config._intolerantFoodSickChance);
            if (worse || sick) {
                int change = Config._rankChangeSick + (complied ? Config._rankChangeSickForced : (byte)0);
                for (Enum.Food food : f) {
                    this._foodRanks.decRankAndCheckFavDislikeChange(food, change);
                }
            }
        }
    }

    private boolean isIntolerant(ArrayList<Enum.Food> f) {
        if (!f.contains((Object)Enum.Food.None)) {
            for (Enum.Food food : f) {
                if (!this._foodRanks.getIntolerant().contains((Object)food)) continue;
                return true;
            }
        }
        return false;
    }

    private void applyNutrition(FoodType f, double modifier) {
        this.setProtein((byte)((double)this._protein + Math.ceil((double)f.getProtein() * modifier)));
        this.setVitamin((byte)((double)this._vitamin + Math.ceil((double)f.getVitamin() * modifier)));
        this.setMineral((byte)((double)this._mineral + Math.ceil((double)f.getMineral() * modifier)));
    }

    private void changeNutrition(byte d) {
        this.setProtein((byte)(this._protein + d));
        this.setVitamin((byte)(this._vitamin + d));
        this.setMineral((byte)(this._mineral + d));
    }

    private int consumablePersonalityMoodChange(Consumable i) {
        int favMod;
        int n = i.getDisposition() != 0 && i.getDisposition() == this._disposition ? Config._consumablePersonalityMatchMoodChange : (favMod = i.getDisposition() != 0 && i.getDisposition() != this._disposition ? Config._consumablePersonalityUnmatchMoodChange : 0);
        favMod += i.getRestless() != 0 && i.getRestless() == this._restless ? Config._consumablePersonalityMatchMoodChange : (i.getRestless() != 0 && i.getRestless() != this._restless ? Config._consumablePersonalityUnmatchMoodChange : 0);
        return favMod += i.getGlutton() != 0 && i.getGlutton() == this._glutton ? Config._consumablePersonalityMatchMoodChange : (i.getGlutton() != 0 && i.getGlutton() != this._glutton ? Config._consumablePersonalityUnmatchMoodChange : 0);
    }

    private boolean processFoodEvol(FoodType food) {
        boolean canEvolve = false;
        if (this.checkFoodReq(food.getID(), food.getEvolProbChange())) {
            this.setCurrentState(Enum.State.Evolving);
            canEvolve = true;
        } else {
            this.setCurrentState(Enum.State.Jeering);
        }
        return canEvolve;
    }

    private boolean processItemEvol(Item item) {
        boolean canEvolve = false;
        if (this.checkItemReq(item.getID(), item.getEvolProbChange())) {
            this.setCurrentState(item.getAnim());
            this.applyItem(item, 1.0);
            item.decQuantity();
            canEvolve = true;
        } else {
            this.setCurrentState(Enum.State.Jeering);
        }
        return canEvolve;
    }

    private boolean checkFoodReq(int food, int evolProbChange) {
        return this._evolution.canEvolve(this) && this.checkEvol(-1, food, false, false, evolProbChange);
    }

    private boolean checkItemReq(int item, int evolProbChange) {
        return this._evolution.canEvolve(this) && this._energy >= Config._requiredDigimentalEnergy && this.checkEvol(item, -1, false, false, evolProbChange);
    }

    private boolean checkMaxHoursBeforeSleep(Consumable c) {
        return c.getMaxHoursBeforeSleep() == -1 || this._asleep || this._sleepLimit - this._sleepLapse <= c.getMaxHoursBeforeSleep();
    }

    public boolean careEffectCanApply(Consumable c) {
        int id = c.getEffectID();
        if (id > -1) {
            CareEffect e = this._careEffects.get(id);
            return e.canApply();
        }
        return true;
    }

    /*
     * Enabled aggressive block sorting
     */
    public Item useItem(Item item) {
        block18: {
            block17: {
                block19: {
                    block20: {
                        if (this._growthStage == Enum.Stage.Egg) break block18;
                        if (item.disturb()) {
                            this.disturb();
                        }
                        if (!this.checkMaxHoursBeforeSleep(item) || item.isMaxBMGauge() && this._bmGauge < this._bmMax || !this._isHome && !(this._world.getCurrentZone().isTown() != null ? item.useInTown() : item.useOutside()) || item.getAdventureLife() > 0 && this._world.getAdventureLife() >= Config._maxAdventureLife || item.getAnim().toString().toLowerCase().contains("transport") && (this._isHome || !this.canTransport(item.getAnim()))) break block19;
                        this.checkRefused(item, null, false, item.getAnim() == Enum.State.ItemEvol ? item.getEnergy() : 0.0);
                        this.checkCompliant();
                        if (this._refused) break block20;
                        this.setDisciplineCall(false);
                        if (item.getAnim() == Enum.State.ItemEvol) {
                            if (item.getID() == 79) {
                                if (this._xAntibodyState == Enum.XAntibodyState.None) {
                                    this.setXAntibodyState(Enum.XAntibodyState.Temporary);
                                }
                                this.xEvolve(item);
                                break block17;
                            } else {
                                if (item.getDigimonID()[0] != -1) {
                                    Random r = new Random();
                                    int i = r.nextInt(item.getDigimonID().length);
                                    this._evolution.digivolve(this._evolution.getDigimon(item.getDigimonID()[i]), this, this._evolution.getEvolDigimon(), false, -1);
                                    this.setCurrentState(Enum.State.ItemEvol);
                                    this.applyItem(item, 1.0);
                                    item.decQuantity();
                                    return item;
                                }
                                this.processItemEvol(item);
                            }
                            break block17;
                        } else {
                            this.setCurrentState(item.getAnim());
                            if (item.getAnim() == Enum.State.X_Program) {
                                boolean survived = Utility.randomChance(Config._xProgramSurvivalChanceTarget, Config._xProgramSurvivalChanceBound);
                                if (this._xAntibodyState == Enum.XAntibodyState.None && !survived) {
                                    this.setLapsedLife(Integer.MAX_VALUE);
                                    this._savedFromDeath = (byte)127;
                                } else if (this._xAntibodyState == Enum.XAntibodyState.None && survived || this._xAntibodyState != Enum.XAntibodyState.None) {
                                    Enum.State remove = item.getAnim();
                                    Item old = item;
                                    Item antibody = this._items.get(79);
                                    item = new Item(Utility.getCSVRecord(Utility.getInputStream(this.getModFolder(), this.MODEL_FOLDER, "items.csv"), old.getID()), antibody.getID(), antibody.getSpriteSet(), antibody.getSpriteNum(), antibody.getAnim());
                                    if (this.xEvolve(item)) {
                                        if (this._currentState == remove) {
                                            this._currentState = Enum.State.Idling;
                                        } else {
                                            this._animQueue.remove((Object)remove);
                                        }
                                        old.decQuantity();
                                        return item;
                                    }
                                    item = old;
                                }
                                this._useWeakConsumable = false;
                                this.setXAntibodyState(Enum.XAntibodyState.XProgram);
                            }
                            if (this._useWeakConsumable && item.getAnim() != Enum.State.Inherit && item.getAnim() != Enum.State.Recover) {
                                this.applyItem(item, Config._weakConsumableCoefficient);
                            } else {
                                this._world.setAdventureLife(this._world.getAdventureLife() + item.getAdventureLife());
                                this.applyItem(item, 1.0);
                            }
                            item.decQuantity();
                        }
                        break block17;
                    }
                    if (this._refused) {
                        this.setCurrentState(Enum.State.Refusing);
                    }
                    break block17;
                }
                this.setCurrentState(Enum.State.Jeering);
            }
            this.autoSave();
        }
        return item;
    }

    private void xAntibodyCountChange(byte currentMin) {
        if (currentMin % Config._xAntibodyCountChangeMin == 0) {
            switch (this._xAntibodyState) {
                case Temporary: {
                    this.setXAntibodyCount(this._xAntibodyCount - 1);
                    break;
                }
                case XProgram: 
                case Permanent: {
                    this.setXAntibodyCount(this._xAntibodyCount + 1);
                }
            }
        }
    }

    private boolean xEvolve(Item item) {
        if (this._xAntibodyState == Enum.XAntibodyState.None) {
            this.setTotalLifespan(this._totalLifespan - (long)this.calcXAntibodyLifeDec());
        }
        if (this.processItemEvol(item)) {
            this.setEnergy((byte)(this._energy + Config._xEvolutionEnergyInc));
            return true;
        }
        if (this._currentState != Enum.State.X_Program) {
            if (this._currentState == Enum.State.Jeering) {
                this._currentState = Enum.State.Idling;
            } else {
                this._animQueue.remove((Object)Enum.State.Jeering);
            }
            this.setCurrentState(Enum.State.X_AntibodyInc);
            this.setCurrentState(Enum.State.Jeering);
            this.applyItem(item, 1.0);
            item.decQuantity();
        }
        return false;
    }

    private int calcXAntibodyLifeDec() {
        int lifeDec = 0;
        if (Utility.randomChance(Config._xAntibodyLifeDecChance, 100)) {
            Random r = new Random();
            int d = r.nextInt(Config._xAntibodyLifeDecModifierBound);
            lifeDec = d == 0 ? 0 : Config._xAntibodyLifeDec / d;
        }
        return lifeDec;
    }

    private void applyFood(FoodType food, boolean complied, Enum.State state) {
        double modifier = (double)(this._hunger - Config._fullHunger) / (double)this.getStomachCapacity();
        modifier = modifier <= 0.0 || food.getHunger() == 0 ? 1.0 : 1.0 - modifier;
        if (this._currentState != state && !this._animQueue.contains((Object)Enum.State.Eating) && !this._animQueue.contains((Object)Enum.State.Assistant_Feed)) {
            if (state == Enum.State.Eating && modifier <= Config._disposeLeftoversMinModifier) {
                state = Enum.State.Munching;
            }
            this.setPriorityState(state);
        }
        if (this._evolution.canFoodEvolve(this._index)) {
            this.processFoodEvol(food);
        }
        if (complied) {
            byte change = 0;
            if (food.getType().contains((Object)this._foodRanks.getDisliked())) {
                change = Config._rankChangeBadFoodForced;
            } else if (this.isIntolerant(food.getType())) {
                change = Config._rankChangeIntolerantForced;
                this.setObedience(this._obedience + Config._obedienceChangeIntolerantForced);
            } else if (complied) {
                change = Config._rankChangeFoodForced;
            }
            if (change > 0) {
                for (Enum.Food f : food.getType()) {
                    this._foodRanks.decRankAndCheckFavDislikeChange(f, change);
                }
            }
        }
        this.setObedience(this._obedience + (int)Math.ceil((double)food.getObedience() * modifier));
        this.setHunger((byte)((double)this._hunger + Math.ceil((double)food.getHunger() * modifier)), food, complied);
        this.applyNutrition(food, modifier);
        this.setBMGauge(this._bmGauge + this._bmLapseInc + (int)Math.ceil((double)food.getBMGauge() * modifier));
        this.applyConsumable(food, modifier);
    }

    private void applyItem(Item item, double modifier) {
        modifier = this.applyItemNoObedience(item, modifier);
        this.setObedience(this._obedience + (int)Math.ceil((double)item.getObedience() * modifier));
    }

    private double applyItemNoObedience(Item item, double modifier) {
        if (item.getDiminishingReturns()) {
            double mod = 1.0 - (double)this._itemInterest / (double)Config._maxItemInterest;
            if (mod < modifier && mod > 0.0) {
                modifier = mod;
            }
        } else {
            modifier = 1.0;
        }
        this.setItemInterest((byte)(this._itemInterest + item.getItemInterestChange()));
        this.setHunger((byte)((double)this._hunger + Math.ceil((double)item.getHunger() * modifier)));
        this.setBMGauge(this._bmGauge + (int)Math.ceil((double)item.getBMGauge() * modifier));
        this.applyConsumable(item, modifier);
        return modifier;
    }

    private void applyConsumable(Consumable item, double modifier) {
        int mood = (int)Math.ceil((double)this.consumablePersonalityMoodChange(item) * modifier);
        if (item.getFavFood() != Enum.Food.None && !this._foodRanks.getIntolerant().contains((Object)item.getFavFood())) {
            this._foodRanks.setFavorite(item.getFavFood());
        }
        if (!this.isFullyRecovered() && item.getRecovered()) {
            this._healthPoints = this._fullHealthPoints;
        }
        if (this.isSick()) {
            if (item.getCureLapseChange() != 0) {
                this.setSickLength((int)((double)this._sickLength + Math.ceil((double)item.getCureLapseChange() * modifier)));
            }
            if (item.getCured()) {
                this.setSickLength(0);
                this.setStateNoRepeat(Enum.State.Cheering);
            }
        }
        if (this.isInj()) {
            if (item.getHealLapseChange() != 0) {
                this.setInjLength((int)((double)this._injLength + Math.ceil((double)item.getHealLapseChange() * modifier)));
            }
            if (item.getHealed()) {
                this.setInjLength(0);
                this.setStateNoRepeat(Enum.State.Cheering);
            }
        }
        if (this.isFatigued()) {
            if (item.getFatigueLapseChange() != 0) {
                this.setFatigueLength((int)((double)this._fatigueLength + Math.ceil((double)item.getFatigueLapseChange() * modifier)));
            }
            if (item.getFatigued()) {
                this.setFatigueLength(0);
            }
        }
        if (this._currentMood == Enum.Mood.Depressed && item.getDepressed()) {
            this._currentMood = Enum.Mood.Neutral;
            this.setMood(Config._undepressedItemFactor);
        }
        if (item.getSleep()) {
            this.setSleepLapse(this._sleepLimit);
        }
        if (item.changeToPrefTemp()) {
            int t = (this._idealTemp[0] + this._idealTemp[1]) / 2;
            this.setTemp(t);
        }
        this.setSleepLapse((int)((double)this._sleepLapse + Math.ceil((double)item.getSleepLapse() * modifier)));
        if (item.getEnergy() != (double)((int)item.getEnergy())) {
            this.setEnergy((byte)((double)this._energy + Math.ceil(item.getEnergy() * (double)this._maxEnergy * modifier)));
        } else {
            this.setEnergy((byte)((double)this._energy + Math.ceil(item.getEnergy() * modifier)));
        }
        this.setRawExercise((byte)((double)this._exercise + Math.ceil((double)item.getStrength() * modifier)));
        this.setEnthusiasm((byte)((double)this._enthusiasm + Math.ceil((double)item.getEnthusiasm() * modifier)));
        this.setMood(this._mood + mood + (int)Math.ceil((double)item.getMood() * modifier));
        this.setCaloriesAndChangeWeight(this._calories + (int)Math.ceil((double)item.getCalories() * modifier));
        this.setWeight(this._weight + (int)Math.ceil((double)item.getWeight() * modifier));
        int seconds = (int)Math.ceil((double)item.getSeconds() * modifier);
        this.setTotalLifespan(this._totalLifespan + (long)seconds);
        this.applyAttributeChange(item, modifier);
        this.setFullHealthPoints((byte)((double)this._fullHealthPoints + Math.ceil((double)item.getHealth() * modifier)));
        if (item.getFavTime() != Enum.Time.None) {
            this._timeRanks.setFavorite(item.getFavTime());
        }
        if (item.getNewPersonality() != Enum.Personality.None) {
            this.changePersonality(item.getNewPersonality());
        }
        if (item.getFavAttribute() != Enum.Attribute.None) {
            this._attributeRanks.setFavorite(item.getFavAttribute());
        }
        int mistake = (int)Math.ceil(item.getMistake() < 0 ? 0.0 : (double)item.getMistake() * modifier);
        this._mistake += mistake;
        if (this._temp + item.getTemp() >= 0 && this._temp + item.getTemp() <= Config._maxTemp) {
            this._temp = (byte)((double)this._temp + Math.ceil((double)item.getTemp() * modifier));
        }
        this._weightRank = (int)((double)this._weightRank + Math.ceil((double)item.getGluttonChange() * modifier));
        this._moodRank = (int)((double)this._moodRank + Math.ceil((double)item.getDispositionChange() * modifier));
        this._energyRank = (int)((double)this._energyRank + Math.ceil((double)item.getRestlessChange() * modifier));
        if (item.getEffectID() != -1) {
            this._careEffects.get(item.getEffectID()).startEffect();
        }
        this._useWeakConsumable = false;
        Random r = new Random();
        if (item.getUnlockedItem().size() > 0) {
            this._unlockConsumable = item.getUnlockedItem().get(r.nextInt(item.getUnlockedItem().size()));
            if (this._unlockConsumable != -1) {
                this.getItemByID(this._unlockConsumable).unlockConsumable(this, Enum.State.UnlockItem);
            }
        } else if (item.getUnlockedFood().size() > 0) {
            this._unlockConsumable = item.getUnlockedFood().get(r.nextInt(item.getUnlockedFood().size()));
            if (this._unlockConsumable != -1) {
                this.getFoodByID(this._unlockConsumable).unlockConsumable(this, Enum.State.UnlockFood);
            }
        }
    }

    private int[] compensateAttributes(int main, int weak, int normal) {
        while (main < 0) {
            if (weak > 0) {
                --weak;
                ++main;
            }
            if (main < 0 && normal > 0) {
                --normal;
                ++main;
            }
            if (weak >= 0 || normal >= 0 || main >= 0) continue;
            main = 0;
            weak = 0;
            normal = 0;
        }
        return new int[]{main, weak, normal};
    }

    private void applyAttributeChange(Consumable item, double modifier) {
        double c = modifier;
        int va = (int)((double)item.getVaccine() * c);
        int d = (int)((double)item.getData() * c);
        int vi = (int)((double)item.getVirus() * c);
        this._vaccinePower += va;
        this._dataPower += d;
        this._virusPower += vi;
        int[] a = this.compensateAttributes(this._vaccinePower, this._dataPower, this._virusPower);
        this._vaccinePower = a[0];
        this._dataPower = a[1];
        this._virusPower = a[2];
        a = this.compensateAttributes(this._dataPower, this._virusPower, this._vaccinePower);
        this._vaccinePower = a[2];
        this._dataPower = a[0];
        this._virusPower = a[1];
        a = this.compensateAttributes(this._virusPower, this._vaccinePower, this._dataPower);
        this._vaccinePower = a[1];
        this._dataPower = a[2];
        this._virusPower = a[0];
    }

    public void transport(Enum.State anim, int id) {
        Zone z = null;
        MapLevel m = this._world.getCurrentMap();
        switch (anim) {
            case BirdraTransport: {
                if (!this._world.toTravelTown()) break;
                this.setCurrentHabitat(this._world.getCurrentZone().getCurrentLocationBackground(), false);
                break;
            }
            case GarudaTransport: {
                z = this._world.getCurrentZone();
                if (z == null) break;
                Enemy e = this._world.getNextBoss();
                if (e != null) {
                    if (e.getZone() != z.getZoneNum() || e.getMap() != m.getMapNum()) {
                        Zone newZone = this._world.getMap(e.getMap()).getZone(e.getZone());
                        this._world.changeZone(z.getIsComplete(), newZone);
                        z = newZone;
                    }
                    int newLoc = e.getLocation()[this._world.getTravelRight() ? 1 : 0];
                    z.setCurrentLocation(newLoc + (this._world.getTravelRight() ? 1 : -1));
                    this._world.setTravelSpeed((byte)0);
                }
                this.setCurrentHabitat(z.getCurrentLocationBackground(), false);
                break;
            }
            case PhoenixTransport: {
                if (id >= m.getZones().size()) break;
                Zone current = this._world.getCurrentZone();
                this._world.changeZone(current.getIsComplete(), m.getZones().get(id));
                this._world.setTravelSpeed((byte)0);
                current = this._world.getCurrentZone();
                ArrayList<Town> towns = this._world.getCurrentZone().getTowns();
                Town t = null;
                if (!towns.isEmpty()) {
                    t = current.getTowns().get(0);
                }
                int l = 0;
                if (t != null) {
                    l = t.getBackgroundRange().getRange()[0];
                }
                current.setCurrentLocation(l);
                this.setCurrentHabitat(current.getCurrentLocationBackground());
                break;
            }
            case WhaTransport: {
                this._world.changeMap(id);
            }
        }
    }

    public void feedVitamin(FoodType f) {
        boolean complied = this.feed(f);
        if (!this._refused) {
            if (this.hasVitamin()) {
                int change = Config._rankChangeSick + (complied ? Config._rankChangeSickForced : (byte)0);
                for (Enum.Food food : f.getType()) {
                    this._foodRanks.decRankAndCheckFavDislikeChange(food, change);
                }
                this.checkWorseSick(Config._vitaminWorseSickChance);
                this.setBMGauge(this._bmGauge + Config._badVitaminBMInc);
                this.setMood(this._mood - Config._badVitaminMoodDec);
                this.setTotalLifespan(this._totalLifespan - (long)Config._badVitaminLifeDec);
                if (this.checkSick(Config._vitaminOverfedSickChance) && complied) {
                    this.setObedience(this._obedience + Config._obedienceChangeSickForced);
                }
                this._mistakeDay += Config._badVitaminMistakeDayChange;
                if (Config._enableLifePenaltyAnim) {
                    this.setStateNoRepeat(Enum.State.Bad_Health_Jeering);
                }
                this.startPoop();
            }
            this.setVitaminLapse(Config._vitaminHours);
            this.autoSave();
        }
    }

    public FoodType getFoodByID(int f) {
        return this._foodTypes.get(f);
    }

    public Item getItemByID(int id) {
        return this._items.get(id);
    }

    private ArrayList<ShopConsumable> getSellableConsumables(ArrayList<Consumable> owned, ArrayList<ShopConsumable> override) {
        ArrayList<ShopConsumable> consumable = new ArrayList<ShopConsumable>();
        ShopConsumable add = null;
        for (Consumable f : owned) {
            if (!f.getCanDecUses() || !f.getCanIncUses() || f.getCurrentUses() / f.getUsesPerConsumable() <= 0) continue;
            if (f.getHomeShop().getResellFactor() > 0 && f.getHomeShop().getPrice() > 0) {
                add = f.getHomeShop();
            }
            if (override != null && add != null) {
                for (ShopConsumable s : override) {
                    if (s.getConsumableID() != add.getConsumableID()) continue;
                    if (s.getResellFactor() > 0 && s.getPrice() > 0) {
                        add = s;
                        break;
                    }
                    add = null;
                    break;
                }
            }
            if (add == null) continue;
            consumable.add(add);
            add = null;
        }
        return consumable;
    }

    public ArrayList<FoodType> getFoodOwned(boolean visibleOnly) {
        ArrayList<FoodType> food = new ArrayList<FoodType>();
        for (FoodType type : this._foodTypes) {
            if (type.getCurrentUses() <= 0 || visibleOnly && !type.getShowInInventory()) continue;
            food.add(type);
        }
        Collections.sort(food, Comparator.comparing(Consumable::isListPriority, Comparator.reverseOrder()));
        return food;
    }

    public ArrayList<ShopConsumable> getSellableFood() {
        Town t;
        ArrayList<ShopConsumable> override = null;
        if (!this._isHome && (t = this._world.getCurrentZone().isTown()) != null) {
            override = t.getFoodOverride();
        }
        return this.getSellableConsumables(this.getFoodTypesAsConsumable(this.getFoodOwned(true)), override);
    }

    public ArrayList<FoodType> getFoodOwned() {
        return this.getFoodOwned(false);
    }

    public ArrayList<Item> getItemsOwned(ArrayList<Item> items) {
        ArrayList<Item> owned = new ArrayList<Item>();
        for (Item item : items) {
            if (item.getCurrentUses() <= 0) continue;
            owned.add(item);
        }
        Collections.sort(owned, Comparator.comparing(Consumable::isListPriority, Comparator.reverseOrder()));
        return owned;
    }

    public ArrayList<ShopConsumable> getSellableItems() {
        Town t;
        ArrayList<ShopConsumable> override = null;
        if (!this._isHome && (t = this._world.getCurrentZone().isTown()) != null) {
            override = t.getItemOverride();
        }
        return this.getSellableConsumables(this.getItemsAsConsumable(this.getItemsOwned(this._items)), override);
    }

    public ArrayList<Item> getNormalItems() {
        return this.getNormalItems(false);
    }

    public ArrayList<Item> getNormalItems(boolean visibleOnly) {
        ArrayList<Item> items = new ArrayList<Item>();
        for (Item item : this._items) {
            if (item.getAnim() == Enum.State.ItemEvol || visibleOnly && !item.getShowInInventory()) continue;
            items.add(item);
        }
        return items;
    }

    public ArrayList<Item> getEvolItems(boolean visibleOnly) {
        ArrayList<Item> items = new ArrayList<Item>();
        for (Item item : this._items) {
            if (item.getAnim() != Enum.State.ItemEvol || visibleOnly && !item.getShowInInventory()) continue;
            items.add(item);
        }
        return items;
    }

    public ArrayList<Item> getEvolItems() {
        return this.getEvolItems(false);
    }

    public boolean canBuy(int price) {
        return this._bits >= price;
    }

    private double[] getObedienceFactors() {
        double obedience = this._currentMood == Enum.Mood.Depressed ? Config._depressedObedience : (double)this._obedience;
        double obedienceFactor = obedience / (double)Config._obedienceRefusalCap;
        double moodMod = Config._obedienceMoodModCoefficient == 0.0 ? 0.0 : (double)this._mood / Config._obedienceMoodModCoefficient * (this._mood < 0 ? 1.0 - obedienceFactor : obedienceFactor);
        double energyFactor = (double)this._energy / (double)this._maxEnergy;
        energyFactor *= 24.0;
        double timeMod = 0.0;
        if (this._timeRanks.getFavorite().equals((Object)this.checkTime(this._clock.getHours()))) {
            timeMod = Config._obedienceTimeModCoefficient;
        } else if (this._timeRanks.getDisliked().equals((Object)this.checkTime(this._clock.getHours()))) {
            timeMod = -Config._obedienceTimeModCoefficient;
        }
        double unwellMod = (this.isSick() || this.isInj() || this.isFatigued() ? Config._refuseUnwellModSickFactor : 0.0) * (1.0 - obedienceFactor);
        double energyMod = obedienceFactor * (this._energy >= 0 ? energyFactor / (this._exercise == 0 ? 1.0 : (double)this._exercise) : energyFactor * (this._exercise == 0 ? 1.0 : (double)this._exercise));
        double enthusiasmMod = (double)this._enthusiasm * Config._obedienceEnthusiasmModCoefficient * (1.0 - obedienceFactor);
        double obey = energyMod + (timeMod *= obedienceFactor) + moodMod + unwellMod + enthusiasmMod;
        return new double[]{obedienceFactor, moodMod, obey};
    }

    public void checkRefused(Consumable type, Enum.Attribute att, boolean isBattle, double energyChange) {
        this.checkRefused(type, att, isBattle, energyChange, Config._canRefuse);
    }

    public void checkRefused(Consumable type, Enum.Attribute att, boolean isBattle, double energyChange, boolean canRefuse) {
        if (this._alive) {
            if (type != null && canRefuse && (type.isForceUse() || this._asleep && type.isForceUseWhenAsleep())) {
                canRefuse = false;
            }
            Random ran = new Random();
            double r = ran.nextInt(Config._refuseChance);
            if (canRefuse && !this._compliance) {
                double[] factors = this.getObedienceFactors();
                double obedienceFactor = factors[0];
                double moodMod = factors[1];
                double obey = 0.0;
                if (type == null) {
                    obey = factors[2];
                }
                if (energyChange != 0.0) {
                    boolean bl = this._refused = (double)this._energy + Math.ceil(energyChange * (double)this._maxEnergy) < 0.0;
                }
                if (!this._refused) {
                    this._refused = type != null ? this.refused(type, obedienceFactor, moodMod, r) : (att != null ? this.refused(att, obey, r) : this.refused(isBattle, obey, r));
                }
                if (this._refused) {
                    this._scold = true;
                }
            } else if (Config._canRefuse && type != null && type.getClass().isInstance(this._items.get(0))) {
                this._useWeakConsumable = true;
            }
        }
    }

    public boolean checkStopTravel() {
        Random ran = new Random();
        double r = (double)ran.nextInt((int)((double)Config._refuseChance * Config._refuseTravelCoefficient)) + (double)Config._obedienceRefusalCap;
        boolean refused = false;
        if (Config._canRefuse && this._energy >= Config._minEnergyForActivity) {
            if (!this._compliance) {
                double obey = this.getObedienceFactors()[2];
                double prob = 0.0;
                double energyMod = 1.0 - (double)(this._maxEnergy - (this._energy + 1)) / (double)this._maxEnergy;
                double travelMod = this._world.getTravelSpeed() == 1 ? Config._refuseTravelModWalkFactor : Config._refuseTravelModRunFactor;
                prob = r * energyMod - (double)this._disposition * Config._refuseTravelDispositionCoefficient + obey - travelMod;
                if (prob <= (double)Config._obedienceRefusalCap - (double)this._obedience) {
                    refused = true;
                }
                if (refused) {
                    this._scold = true;
                }
            }
        } else if (this._energy < Config._minEnergyForActivity) {
            this._world.setTravelSpeed((byte)0);
            this.setCurrentState(Enum.State.Jeering);
        }
        return refused;
    }

    public boolean checkCompliant() {
        boolean complied = this._compliance;
        this.setCompliance(false);
        return complied;
    }

    private boolean refused(Consumable type, double obedienceFactor, double moodMod, double r) {
        boolean refused = false;
        double obedience = this.getAdjustedObedience();
        switch (type.getClass().getName()) {
            case "Model.FoodType": {
                FoodType t = (FoodType)type;
                if (!t.getType().contains((Object)this._foodRanks.getFavorite()) || this._hunger > Config._fullHunger) {
                    double medMod = t.getType().contains((Object)Enum.Food.Med) ? (double)Config._refuseMedFactor * (1.0 - obedienceFactor) : 0.0;
                    double favMod = 0.0;
                    if (t.getType().contains((Object)this._foodRanks.getDisliked())) {
                        favMod = (double)this._hunger / (double)this.getStomachCapacity() * Config._refuseDislikedFoodCoefficient;
                    } else if (t.getType().contains((Object)this._foodRanks.getFavorite())) {
                        favMod = (1.0 - (double)this._hunger / (double)this.getStomachCapacity()) * Config._refuseFavModStomachCoefficient;
                    }
                    favMod += t.getDisposition() != 0 && t.getDisposition() == this._disposition ? Config._refuseFavModDispositionMatchFactor : (t.getDisposition() != 0 && t.getDisposition() != this._disposition ? Config._refuseFavModDispositionUnmatchFactor : 0.0);
                    favMod += t.getRestless() != 0 && t.getRestless() == this._restless ? Config._refuseFavModRestlessMatchFactor : (t.getRestless() != 0 && t.getRestless() != this._restless ? Config._refuseFavModRestlessUnmatchFactor : 0.0);
                    double unwellMod = (this.isSick() ? Config._refuseUnwellModSickFactor : 0.0) * (1.0 - obedienceFactor);
                    double hungerMod = (double)this._hunger / (double)this.getStomachCapacity() * (this._glutton == 0 ? Config._refuseHungerModCoefficient : (this._glutton == 1 ? Config._refuseGluttonHungerModCoefficient : Config._refuseNotGluttonHungerModCoefficient));
                    double obey = unwellMod + (favMod += t.getGlutton() != 0 && t.getGlutton() == this._glutton ? Config._refuseFavModGluttonMatchFactor : (t.getGlutton() != 0 && t.getGlutton() != this._glutton ? Config._refuseFavModGluttonUnmatchFactor : 0.0)) + hungerMod + moodMod + medMod;
                    if (!(r >= obedience + obey)) break;
                    refused = true;
                    break;
                }
                if (this._refused) {
                    this.spoil();
                }
                this.setRefused(false);
                break;
            }
            case "Model.Item": {
                double favMod;
                double medMod;
                Item i = (Item)type;
                double d = medMod = i.getCured() || i.getHealed() ? (double)Config._refuseMedFactor * (1.0 - obedienceFactor) : 0.0;
                double d2 = i.getDisposition() != 0 && i.getDisposition() == this._disposition ? Config._refuseFavModDispositionMatchFactor : (favMod = i.getDisposition() != 0 && i.getDisposition() != this._disposition ? Config._refuseFavModDispositionUnmatchFactor : 0.0);
                favMod += i.getRestless() != 0 && i.getRestless() == this._restless ? Config._refuseFavModRestlessMatchFactor : (i.getRestless() != 0 && i.getRestless() != this._restless ? Config._refuseFavModRestlessUnmatchFactor : 0.0);
                double d3 = i.getGlutton() != 0 && i.getGlutton() == this._glutton ? Config._refuseFavModGluttonMatchFactor : (i.getGlutton() != 0 && i.getGlutton() != this._glutton ? Config._refuseFavModGluttonUnmatchFactor : 0.0);
                double unwellMod = (this.isSick() ? Config._refuseUnwellModSickFactor : 0.0) * (1.0 - obedienceFactor);
                double interestMod = i.getItemInterestChange() > 0 ? (double)this._itemInterest * Config._refuseInterestModCoefficient : 0.0;
                double obey = unwellMod + (favMod += d3) + moodMod + interestMod + medMod;
                if (!(r >= obedience + obey)) break;
                refused = true;
            }
        }
        return refused;
    }

    private boolean refused(Enum.Attribute attribute, double obey, double r) {
        boolean refused = false;
        double obedience = this.getAdjustedObedience();
        if (attribute != this._attributeRanks.getFavorite()) {
            if (attribute != Enum.Attribute.None && attribute == this._attributeRanks.getDisliked()) {
                obey += (double)Config._dislikedAttributeObeyChange;
            }
            if (r >= obedience + obey) {
                refused = true;
            }
        } else if (this._enthusiasm <= 0) {
            if (r >= obedience + Config._exerciseRefuseLowEnthusiasmFactor + obey) {
                refused = true;
            }
        } else {
            if (this._refused) {
                this.spoil();
            }
            this.setRefused(false);
        }
        return refused;
    }

    private boolean refused(boolean isBattle, double obey, double r) {
        boolean refused = false;
        double obedience = this.getAdjustedObedience();
        if (isBattle) {
            if (this._disposition == 0 || this._disposition == 1) {
                if (r + (double)this._disposition * Config._highDispositionBattleObedienceDispositionCoefficient >= obedience + obey) {
                    refused = true;
                }
            } else if (r >= obedience + Config._lowDispositionBattleObedienceFactor + obey) {
                refused = true;
            }
        } else if (r <= (double)Config._obedienceRefusalCap - obedience) {
            refused = true;
        }
        return refused;
    }

    private boolean refused(Battle battle, double obey, double r) {
        double refusalChance;
        double obedienceChance;
        boolean refused = false;
        double obedience = this.getAdjustedObedience();
        if (this._disposition == 0 || this._disposition == 1) {
            obedienceChance = obedience + obey + ((double)battle.getHealth() >= (double)this._fullHealthPoints / Config._obedienceChanceHealthCoefficient ? Config._highDispositionObedienceChanceHighHealthFactor : Config._highDispositionObedienceChanceLowHealthFactor);
            refusalChance = r + (double)this._disposition * Config._highDispositionRefuseChanceDispositionCoefficient;
        } else {
            obedienceChance = obedience + obey + ((double)battle.getHealth() >= (double)this._fullHealthPoints / Config._obedienceChanceHealthCoefficient ? Config._lowDispositionObedienceChanceHighHealthFactor : Config._lowDispositionObedienceChanceLowHealthFactor);
            refusalChance = r + (battle.getHealth() >= battle.getEnemyHealth() ? Config._lowDispositionRefuseChanceLowEnemyHealthFactor : Config._lowDispositionRefuseChanceHighEnemyHealthFactor);
        }
        if (refusalChance >= obedienceChance) {
            refused = true;
        }
        return refused;
    }

    private double getAdjustedObedience() {
        double obedience = this._obedience;
        if (this._currentMood == Enum.Mood.Depressed && Config._depressedObedience < obedience) {
            obedience = Config._depressedObedience;
        }
        return obedience;
    }

    public void checkSurrender(Battle battle) {
        int surrender = 0;
        if (Config._canRefuse) {
            double continueChance = 0.0;
            double surrenderChance = 0.0;
            double[] obedienceFactors = this.getObedienceFactors();
            double obey = obedienceFactors[2];
            Random ran = new Random();
            double r = ran.nextInt(Config._refuseChance);
            int currentHealth = battle.getHealth();
            int enemyHealth = battle.getEnemyHealth();
            Enemy e = battle.getEnemy();
            if (this._disposition == 0 || this._disposition == 1) {
                continueChance = this.getAdjustedObedience() + obey + ((double)currentHealth >= (double)this._fullHealthPoints / Config._surrenderChanceHealthCoefficient ? Config._highDispositionContinueChanceHighHealthFactor : Config._highDispositionContinueChanceLowHealthFactor) + (currentHealth < enemyHealth && (double)enemyHealth >= (double)e.getEnemyHealth() / Config._surrenderChanceHealthCoefficient ? Config._highDispositionContinueChanceHighEnemyHealthFactor : Config._highDispositionContinueChanceLowEnemyHealthFactor);
                surrenderChance = r + (double)this._disposition * Config._surrenderChanceDispositionCoefficient + ((double)currentHealth >= (double)this._fullHealthPoints / Config._surrenderChanceHealthCoefficient && currentHealth >= enemyHealth ? Config._highDispositionSurrenderChanceHighHealthFactor : Config._highDispositionSurrenderChanceLowHealthFactor);
            } else {
                continueChance = this.getAdjustedObedience() + obey + ((double)currentHealth >= (double)this._fullHealthPoints / Config._surrenderChanceHealthCoefficient ? Config._lowDispositionContinueChanceHighHealthFactor : Config._lowDispositionContinueChanceLowHealthFactor);
                surrenderChance = r + ((double)currentHealth >= (double)this._fullHealthPoints / Config._surrenderChanceHealthCoefficient && currentHealth >= enemyHealth ? Config._lowDispositionSurrenderChanceLowEnemyHealthFactor : Config._lowDispositionSurrenderChanceHighEnemyHealthFactor);
            }
            if (surrenderChance >= continueChance) {
                surrender = 2;
                double factor = (double)currentHealth >= (double)this._fullHealthPoints / Config._surrenderChanceHealthCoefficient && (currentHealth >= enemyHealth || (double)currentHealth / (double)this._fullHealthPoints >= (double)enemyHealth / (double)e.getEnemyHealth()) ? Config._surrenderChanceHighFactor : (this._battles > 0 && (double)this._wins / (double)this._battles >= Config._surrenderChanceHighFactorWinRateMin ? Config._surrenderChanceHighFactor : Config._surrenderChanceLowFactor);
                r = ran.nextInt(Config._refuseChance);
                surrenderChance = (r + (double)this._disposition * Config._surrenderChanceDispositionCoefficient - (currentHealth < enemyHealth && (double)enemyHealth >= (double)e.getEnemyHealth() / Config._surrenderChanceHealthCoefficient ? Config._surrenderChanceHighEnemyHealthFactor : Config._surrenderChanceLowEnemyHealthFactor)) / factor;
                if (surrenderChance >= continueChance) {
                    surrender = 1;
                }
            }
        }
        this._surrender = surrender;
    }

    private void spoil() {
        this.setObedience(this._obedience - Config._spoilObedienceDec);
        this.setMood(this._mood + Config._spoilMoodInc);
    }

    public boolean isSunset(Enum.Time t) {
        if (t == Enum.Time.Noon) {
            byte hour = this._clock.getHours();
            Habitat h = this.getCurrentHabitat();
            switch (this.getSeason()) {
                case Spring: {
                    return hour == h.getSpringTime()[2] - 1;
                }
                case Summer: {
                    return hour == h.getSummerTime()[2] - 1;
                }
                case Fall: {
                    return hour == h.getFallTime()[2] - 1;
                }
            }
            return hour == h.getWinterTime()[2] - 1;
        }
        return false;
    }

    public Enum.Time checkTime(int hour) {
        Enum.Time time = Enum.Time.None;
        Habitat h = this._habitats.get(this._currentHabitat);
        switch (this.getSeason()) {
            case Spring: {
                if (hour >= h.getSpringTime()[0] && hour < h.getSpringTime()[1]) {
                    time = Enum.Time.Morning;
                    break;
                }
                if (hour >= h.getSpringTime()[1] && hour < h.getSpringTime()[2]) {
                    time = Enum.Time.Noon;
                    break;
                }
                time = Enum.Time.Night;
                break;
            }
            case Summer: {
                if (hour >= h.getSummerTime()[0] && hour < h.getSummerTime()[1]) {
                    time = Enum.Time.Morning;
                    break;
                }
                if (hour >= h.getSummerTime()[1] && hour < h.getSummerTime()[2]) {
                    time = Enum.Time.Noon;
                    break;
                }
                time = Enum.Time.Night;
                break;
            }
            case Fall: {
                if (hour >= h.getFallTime()[0] && hour < h.getFallTime()[1]) {
                    time = Enum.Time.Morning;
                    break;
                }
                if (hour >= h.getFallTime()[1] && hour < h.getFallTime()[2]) {
                    time = Enum.Time.Noon;
                    break;
                }
                time = Enum.Time.Night;
                break;
            }
            case Winter: {
                time = hour >= h.getFallTime()[0] && hour < h.getFallTime()[1] ? Enum.Time.Morning : (hour >= h.getFallTime()[1] && hour < h.getFallTime()[2] ? Enum.Time.Noon : Enum.Time.Night);
            }
        }
        return time;
    }

    public void praise() {
        if (this._growthStage != Enum.Stage.Egg) {
            this.disturb();
            this.setDisciplineCall(false);
            this.setMood(this._mood + (this._disposition < 0 ? Config._praiseLowDispositionMoodInc : Config._praiseHighDispositionMoodInc));
            if (!this._compliance) {
                this.setObedience(this._obedience - Config._praiseNoncompliantObedienceDec);
            }
            boolean badPraise = false;
            if (this._scoldWindow <= this.scaleToClock(Config._scoldWindowMax) && this._scold && !this._praise) {
                this.setMood(this._mood + Config._praiseScoldMoodInc);
                this.setEnthusiasm(Config._praiseScoldEnthusiasmChange);
                this.setObedience(this._obedience - Config._praiseScoldObedienceDec);
                this.setScoldWindow((byte)0);
                badPraise = true;
            } else if (this._praiseWindow <= this.scaleToClock(Config._praiseWindowMax) && this._praise) {
                this.setObedience(this._obedience + (this._disposition == 0 ? Config._correctPraiseObedienceInc : (this._disposition > 0 ? Config._correctPraiseObedienceIncHighDisposition : Config._correctPraiseObedienceIncLowDisposition)));
                this.setPraiseWindow((byte)0);
            }
            if (badPraise) {
                this.setCurrentState(Enum.State.Bad_Praise);
            } else {
                this.setCurrentState(Enum.State.Cheering);
            }
        }
    }

    public void scold() {
        if (this._growthStage != Enum.Stage.Egg) {
            this.disturb();
            this.setObedience(this._obedience + Config._scoldObedienceInc);
            if (this._obedience < Config._scoldHighObedienceMood) {
                this.setMood(this._mood - Config._scoldLowObedienceMoodDec);
            } else {
                this.setMood(this._mood - Config._scoldHighObedienceMoodDec);
            }
            boolean badScold = false;
            if (this._praiseWindow <= this.scaleToClock(Config._praiseWindowMax) && this._praise && !this._scold) {
                this.setMood(this._mood - Config._scoldPraiseMoodDec);
                this.setEnthusiasm((byte)(this._enthusiasm - Config._scoldPraiseEnthusiasmDec));
                this.setObedience(this._obedience + (this._disposition > 0 ? Config._scoldPraiseObedienceIncHighDisposition : (this._disposition < 0 ? Config._scoldPraiseObedienceIncLowDisposition : Config._scoldPraiseObedienceInc)));
                this.setPraiseWindow((byte)0);
                badScold = true;
            } else if (this._scoldWindow <= this.scaleToClock(Config._scoldWindowMax) && this._scold) {
                this.setEnthusiasm((byte)(this._enthusiasm + Config._correctScoldEnthusiasmChange));
                this.setObedience(this._obedience + (this._disposition == 0 ? Config._correctScoldObedienceInc : (this._disposition > 0 ? Config._correctScoldObedienceIncHighDisposition : Config._correctScoldObedienceIncLowDisposition)));
                this.setScoldWindow((byte)0);
                this.setCompliance(true);
                this.setRefused(false);
            } else {
                this.setEnthusiasm((byte)(this._enthusiasm + Config._scoldEnthusiasmChange));
            }
            if (badScold) {
                this.setCurrentState(Enum.State.Bad_Scold);
            } else {
                this.setCurrentState(Enum.State.Jeering);
            }
            this.scoldDisciplineCall();
        }
    }

    private void scoldDisciplineCall() {
        if (this._disciplineCall) {
            this._disciplineCall = !this._disciplineCall;
            this._compliance = false;
            this.setObedience(this._obedience + Config._disciplineCallScoldObedienceInc);
            this._callMinutesDiscipline = 0;
            this.autoSave();
        }
    }

    public void exercise(Enum.Attribute trainingAttribute, boolean complied) {
        if (this._growthStage != Enum.Stage.Egg) {
            this.setDisciplineCall(false);
            if (trainingAttribute == Enum.Attribute.None) {
                this.setExercise((byte)(this._exercise + 1), null, Config._rankChangeFatigue, complied);
            } else {
                this.setExercise((byte)(this._exercise + 1), trainingAttribute, 0, complied);
            }
            if (trainingAttribute == this._attributeRanks.getFavorite()) {
                this._attributeRanks.setUnlockedFav(true);
                this.setEnthusiasm((byte)(this._enthusiasm - Config._exerciseFavAttributeEnthusiasmDec));
            } else if (trainingAttribute == Enum.Attribute.None && this._disposition == -1) {
                this.setEnthusiasm((byte)(this._enthusiasm - Config._exerciseFavAttributeEnthusiasmDec));
            } else if (trainingAttribute == this._attributeRanks.getDisliked()) {
                this._attributeRanks.setUnlockedDislike(true);
                this.setEnthusiasm((byte)(this._enthusiasm + Config._exerciseDislikedAttributeEnthusiasmChange + (complied ? Config._enthusiasmChangeDislikeForced : (byte)0)));
            } else {
                this.setEnthusiasm((byte)(this._enthusiasm - Config._exerciseNotFavAttributeEnthusiasmDec));
            }
            this.checkExerciseTime();
            this.setMood(this._mood + this._enthusiasm);
            if (this.checkWorseSick(Config._exerciseWorseSickChance) && complied) {
                this.setObedience(this._obedience + Config._obedienceChangeSickForced);
            }
            this.checkExerciseInj(trainingAttribute, complied);
            this.setWeight(this._weight - Config._exerciseWeightDec);
            this.setCaloriesAndChangeWeight(this._calories - Config._exerciseCalorieDec);
            this.setEnergy((byte)(this._energy - Config._exerciseEnergyDec));
        }
    }

    public Enum.Time incExerciseTime() {
        Enum.Time time = this.checkTime(this._clock.getHours());
        switch (time) {
            case Morning: {
                ++this._morningTrain;
                break;
            }
            case Noon: {
                ++this._dayTrain;
                break;
            }
            default: {
                ++this._nightTrain;
            }
        }
        return time;
    }

    private void checkExerciseTime() {
        Enum.Time time = this.incExerciseTime();
        this._timeRanks.changeRank(time);
        if (this._timeRanks.getFavorite().equals((Object)time)) {
            this._timeRanks.setUnlockedFav(true);
            this.setMood(this._mood + Config._favExerciseTimeMoodInc);
            this.setEnthusiasm((byte)(this._enthusiasm + Config._favExerciseTimeEnthusiasmChange));
        } else if (this._timeRanks.getDisliked().equals((Object)time)) {
            this._timeRanks.setUnlockedDislike(true);
            this.setMood(this._mood - Config._notFavExerciseTimeMoodDec);
            this.setEnthusiasm((byte)(this._enthusiasm + Config._dislikedTimeExerciseEnthusiasmChange));
        } else {
            this.setMood(this._mood - Config._notFavExerciseTimeMoodDec);
        }
    }

    public void applyDNA(Enum.Field f, int quantity) {
        if (this._dna.applyDNA(f, quantity)) {
            this.disturb();
            if (this._exercise + Config._dnaStrengthChange * quantity < this.getExerciseLimit()) {
                this.setExercise((byte)(this._exercise + Config._dnaStrengthChange * quantity));
            } else {
                this.setExercise((byte)(this.getExerciseLimit() - 1));
            }
            if (f == this._field) {
                this.setMood(this._mood + Config._dnaSameFieldMood * quantity);
                this.setEnthusiasm((byte)(this._enthusiasm - Config._dnaSameFieldEnthusiasmDec * quantity));
                this.checkWorseSick(Config._dnaSameFieldWorseSickChance * quantity);
                this.checkSick(Config._dnaSameFieldSickChance * quantity);
            } else {
                this.setMood(this._mood + Config._dnaDiffFieldMood * quantity);
                this.setEnthusiasm((byte)(this._enthusiasm - Config._dnaDiffFieldEnthusiasmDec * quantity));
                this.checkWorseSick(Config._dnaDiffFieldWorseSickChance * quantity);
                this.checkSick(Config._dnaDiffFieldSickChance * quantity);
            }
            this.setCurrentState(Enum.State.DNA_Feeding);
            this.autoSave();
        } else {
            this.setCurrentState(Enum.State.Jeering);
        }
    }

    public boolean canExercise(Enum.Attribute att) {
        boolean canTrain = false;
        if (this._growthStage != Enum.Stage.Egg) {
            this.disturb(att);
            if (att != Enum.Attribute.None) {
                this.checkRefused(null, att, false, 0.0);
            } else {
                this.checkRefused(null, null, true, 0.0);
            }
            if (this._energy >= Config._minEnergyForActivity && !this._refused) {
                canTrain = true;
                switch (att) {
                    case Vaccine: {
                        this.setCurrentState(Enum.State.Vaccine_Training);
                        break;
                    }
                    case Data: {
                        this.setCurrentState(Enum.State.Data_Training);
                        break;
                    }
                    case Virus: {
                        this.setCurrentState(Enum.State.Virus_Training);
                        break;
                    }
                    case None: {
                        this.setCurrentState(Enum.State.HP_Training);
                    }
                }
            } else if (this._refused) {
                this.setCurrentState(Enum.State.Refusing);
            } else {
                this.setCurrentState(Enum.State.Jeering);
            }
        }
        return canTrain;
    }

    public void feedMed(FoodType f) {
        boolean complied = this.feed(f);
        if (this.isSick() && !this._refused) {
            if (this.getMed()) {
                int change = Config._rankChangeSick + (complied ? Config._rankChangeSickForced : (byte)0);
                for (Enum.Food food : f.getType()) {
                    this._foodRanks.decRankAndCheckFavDislikeChange(food, change);
                }
                this._mistakeDay += Config._badMedMistakeDayChange;
                this.setTotalLifespan(this._totalLifespan - (long)Config._badMedLifeDec);
                this.setBMGauge(this._bmGauge + Config._badMedBMInc);
                if (Config._enableLifePenaltyAnim) {
                    this.setStateNoRepeat(Enum.State.Bad_Health_Jeering);
                }
                this.startPoop();
            } else {
                this.setMood(this._mood + Config._curedMoodBonus / Config._sickLength);
                this.setObedience(this._obedience + Config._curedObedienceBonus / Config._sickLength);
                this.setMedLapse(Config._medicineHours);
            }
        }
    }

    public void applyBandage(Item i) {
        if (this.isInj()) {
            if (!this.getBandage()) {
                this.useItem(i);
                if (!this._refused) {
                    this.setMood(this._mood + Config._curedMoodBonus / Config._injLength);
                    this.setObedience(this._obedience + Config._curedObedienceBonus / Config._injLength);
                    this.setBandageLapse(Config._bandageHours);
                }
            } else {
                this.setCurrentState(Enum.State.Jeering);
            }
        }
    }

    public boolean canEvolve(int index, boolean connecting) {
        return this._evolution.checkEvolReq(this, this._evolution.getDigimon(index), connecting, 0);
    }

    public String canJogress() {
        String jogressMatch = "";
        this.disturb();
        EvolutionInfo character = this._evolution.getDigimon(this._index);
        jogressMatch = this._evolution.checkJogress(this, character);
        if (this._energy < Config._requiredJogressEnergy) {
            jogressMatch = "";
        }
        if (jogressMatch.equals("")) {
            this.setCurrentState(Enum.State.Jeering);
        } else {
            this.checkRefused(null, null, true, Config._jogressEnergyChange);
            this.checkCompliant();
            if (this._refused) {
                jogressMatch = "";
                this.setCurrentState(Enum.State.Refusing);
            }
        }
        return jogressMatch;
    }

    public boolean canTeleport() {
        boolean canTransport;
        this.disturb();
        this.checkRefused(null, null, true, 0.0);
        this.checkCompliant();
        boolean bl = canTransport = !this._refused;
        if (!canTransport) {
            this.setCurrentState(Enum.State.Refusing);
        } else if (this._world.getCurrentMap() == null) {
            canTransport = false;
            this.setCurrentState(Enum.State.Jeering);
        }
        return canTransport;
    }

    /*
     * Enabled force condition propagation
     * Lifted jumps to return sites
     */
    private boolean canTransport(Enum.State anim) {
        boolean canTransport = false;
        if (anim == null) return canTransport;
        int loc = this._world.getCurrentZone().getCurrentLocation();
        switch (anim) {
            case BirdraTransport: {
                Town town;
                BackgroundRange t;
                boolean inTown = false;
                Iterator<Town> iterator = this._world.getCurrentZone().getTowns().iterator();
                while (iterator.hasNext() && (inTown = (t = (town = iterator.next()).getBackgroundRange()).getRange()[0] <= loc && t.getRange()[1] >= loc)) {
                }
                if (inTown) return false;
                if (!this._world.isTownClose()) return false;
                return true;
            }
            case GarudaTransport: {
                Enemy e = this._world.getNextBoss();
                if (e == null) return false;
                if (this._world.getTravelRight()) {
                    if (e.getLocation()[1] != loc - 1) {
                        return true;
                    }
                } else if (e.getLocation()[0] != loc + 1) return true;
                if (e.getMap() != this._world.getCurrentMap().getMapNum()) return true;
                if (e.getZone() == this._world.getCurrentZone().getZoneNum()) return false;
                return true;
            }
            case PhoenixTransport: {
                return true;
            }
            case WhaTransport: {
                return true;
            }
        }
        return canTransport;
    }

    public boolean canBattle(boolean isTourney) {
        boolean canBattle = false;
        if (this._growthStage != Enum.Stage.Egg) {
            this.disturb(Config._rankChangeDisturb);
            this.setDisciplineCall(false);
            this.checkRefused(null, null, true, 0.0);
            if (this._energy >= Config._minEnergyForActivity && !this._refused) {
                this._praise = false;
                canBattle = true;
                if (!isTourney) {
                    this.setCurrentState(Enum.State.Battle_Flash);
                }
            } else if (this._refused) {
                this.setCurrentState(Enum.State.Refusing);
            } else {
                this.setCurrentState(Enum.State.Jeering);
            }
        }
        return canBattle;
    }

    public boolean refuseAttack(Battle battle) {
        boolean refuseAttack = false;
        if (Config._canRefuse) {
            double[] factors = this.getObedienceFactors();
            Random ran = new Random();
            double r = ran.nextInt(Config._refuseChance);
            refuseAttack = this.refused(battle, factors[2], r);
        }
        return refuseAttack;
    }

    public void canTravel() {
        if (this._world.getTravelSpeed() != 0) {
            this.checkRefused(null, null, true, 0.0);
            this.checkCompliant();
            if (this._refused) {
                this.setCurrentState(Enum.State.Refusing);
                this._world.setTravelSpeed((byte)0);
            }
        } else if (this._world.getTravelSpeed() == 0) {
            this.setRefused(false);
            this.setScoldWindow((byte)0);
        }
    }

    public boolean isUnwell() {
        boolean unwell = false;
        if (this.isSick() || this.isInj() || this.isFatigued()) {
            unwell = true;
        }
        return unwell;
    }

    public void clean() {
        if (this._alive && this.isFilth()) {
            this._callMinutesPoop = 0;
            this.cleanMoodIncrease();
            this.setObedience(this._obedience + (this._disposition > 0 ? Config._cleanObedienceIncHighDisposition : (this._disposition < 0 ? Config._cleanObedienceIncLowDisposition : Config._cleanObedienceInc)));
        }
        this.setCurrentState(Enum.State.Cleaning);
    }

    public void cleanMoodIncrease() {
        this.setMood(this._mood + Config._cleanMoodInc);
    }

    public void lightSwitch() {
        this.setLights(!this._lights);
        if (this._alive && !this._paused && this._growthStage != Enum.Stage.Egg) {
            if (this._lights && this._nap && !this.isFuton()) {
                this.setAsleep(false);
                if (this.isSick() || this.isInj()) {
                    this.setSleepLapse(this._sleepLapse + 1);
                }
                this.setAwakeLapse(0);
            } else if (!this._lights) {
                this.setDisciplineCall(false);
            }
        }
    }

    private void checkDepressed(byte currentMin) {
        if (this._growthStage != Enum.Stage.Egg && currentMin % Config._depressedLapseMin == 0) {
            Random ran = new Random();
            int r = ran.nextInt(Config._depressedChance);
            if (this._currentMood == Enum.Mood.Depressed) {
                if (r < Config._undepressedNegativeMoodChance && this._mood < 0) {
                    this._currentMood = Enum.Mood.Unhappy;
                    this.setMood(Config._newUndepressedMood);
                } else if (r < Config._undepressedPositiveMoodChance && this._mood > 0) {
                    this._currentMood = Enum.Mood.Unhappy;
                    this.setObedience(this._obedience + Config._undepressedObedienceInc);
                    this.setMood(Config._newUndepressedMood);
                } else {
                    this.setMood(this._mood + Config._depressedMoodChange);
                    this.setObedience(this._obedience + Config._depressedObedienceChange);
                    this.setEnthusiasm((byte)(this._enthusiasm + Config._depressedEnthusiasmChange));
                }
            } else if (this._currentMood == Enum.Mood.Unhappy && this._growthStage != Enum.Stage.Fresh && this._growthStage != Enum.Stage.InTraining) {
                if (this._mood <= Config._toDepressedMoodMin && r < Config._negativeMoodDepressedChance) {
                    this._currentMood = Enum.Mood.Depressed;
                } else if (r < Config._normalMoodDepressedChance) {
                    this._currentMood = Enum.Mood.Depressed;
                }
            }
        }
    }

    private void checkDisciplineCall(byte currentMin) {
        if (!(this._growthStage == Enum.Stage.Egg || currentMin % Config._disciplineCallMin != 0 || !this._alive || this._toNapSleepLapse + 1 >= this.calcToSleepNapLapse() || this._sleepLapse + 1 >= this._sleepLimit || this._asleep || this._obedience >= Config._disciplineCallObedienceMax && this._growthStage != Enum.Stage.Fresh && this._growthStage != Enum.Stage.InTraining || this.checkCall())) {
            int mod = 0;
            if (this._hunger < Config._fullHunger && this._glutton > 0) {
                mod = 3;
            } else if (this._hunger < Config._fullHunger && this._glutton < 0) {
                mod = -1;
            }
            if (this._exercise < Config._fullStrength && this._restless > 0) {
                mod = 3;
            } else if (this._exercise < Config._fullStrength && this._restless < 0) {
                mod = -1;
            }
            if (Utility.randomChance(Config._disciplineCallTargetChance + mod, Config._disciplineChance - (Config._obedienceRefusalCap - this._obedience))) {
                this._disciplineCall = true;
                if (this._clock.canResetClockSpeed() && Config._enableFastForward && Config._resetClockSpeedOnCall) {
                    this._clock.setFastMod(1);
                }
                this.setScoldWindow((byte)0);
                this._scold = true;
            }
        }
    }

    private void enthusiasmLapse(byte currentMin) {
        if (this._growthStage != Enum.Stage.Egg && currentMin % Config._enthusiasmLapseMin == 0) {
            if (!this._asleep) {
                this.setMood(this._mood - Math.abs((int)Math.ceil((double)this._enthusiasm * Config._enthusiasmMoodDecCoefficient)));
                this.setEnthusiasm((byte)(this._enthusiasm + (this._energy > this._maxEnergy / Config._enthusiasmChangeEnergyCoefficient ? Config._highEnergyEnthusiasmChange : Config._lowEnergyEnthusiasmChange)));
            } else if (this._enthusiasm > 0) {
                this.setEnthusiasm((byte)(this._enthusiasm - Config._enthusiasmLapseDec));
            } else if (this._enthusiasm < 0) {
                this.setEnthusiasm((byte)(this._enthusiasm + Config._enthusiasmLapseInc));
            }
        }
    }

    public void obedienceLapse(byte currentMin) {
        if (!(this._growthStage == Enum.Stage.Egg || this._asleep && this._obedience <= Config._minObedienceAsleep)) {
            this._obedienceChangeLapse = (byte)(this._obedienceChangeLapse + 1);
            if (this._obedienceChangeLapse >= (this._disposition > 0 ? Config._obedienceLapseMinHighDisposition : (this._disposition < 0 ? (int)Config._obedienceLapseMinLowDisposition : (int)Config._obedienceLapseMin))) {
                this.checkObedienceDec();
                this._obedienceChangeLapse = 0;
            }
        }
    }

    private void checkObedienceDec() {
        this.setObedience(this._obedience - (this._disposition > 0 ? Config._obedienceLapseDecHighDisposition : (this._disposition < 0 ? Config._obedienceLapseDecLowDisposition : Config._obedienceLapseDec)));
        if (this._obedience < 0) {
            this._obedience = 0;
        }
        if (this.isFilth()) {
            this.setObedience(this._obedience + Config._obedienceChangeFilthScale * this.countFilth());
        }
    }

    public byte checkIsRain() {
        byte isRain = 0;
        switch (this._currentWeather) {
            case Snowing: 
            case LightSnow: 
            case HeavySnow: {
                isRain = 0;
                break;
            }
            case Raining: 
            case Drizzling: 
            case HeavyRain: {
                isRain = 1;
                break;
            }
            default: {
                isRain = 2;
            }
        }
        return isRain;
    }

    public boolean checkNiceWeather(byte isRain) {
        return (this._field.equals((Object)Enum.Field.DeepSaver) || this._element.equals((Object)Enum.Element.Water)) && isRain == 1 || (this._idealTemp[0] <= Config._freezingTemp || this._element.equals((Object)Enum.Element.Ice)) && isRain == 0;
    }

    public void checkAllWeather(byte currentMin) {
        if (currentMin % Config._weatherCheckMin == 0) {
            WeatherRecord skip = this.checkCurrentWeather();
            ArrayList<WeatherRecord> remove = new ArrayList<WeatherRecord>();
            if (skip != null && skip.getWeather() == Enum.Weather.Clear) {
                remove.add(skip);
            }
            for (int i = 0; i < this._weatherRecord.size(); ++i) {
                WeatherRecord wr = this._weatherRecord.get(i);
                if (wr == skip) continue;
                wr.setWeather(this.checkWeather(wr.getWeather(), this._habitats.get(wr.getHabitat())));
                if (wr.getWeather() != Enum.Weather.Clear) continue;
                remove.add(wr);
            }
            for (WeatherRecord i : remove) {
                this._weatherRecord.remove(i);
            }
        }
    }

    public void transitionWeather(Enum.Weather oldWeather) {
        if (this._currentWeather == Enum.Weather.Clear) {
            this.setDayTemp();
            Random r = new Random();
            int p = r.nextInt(2);
            switch (oldWeather) {
                case HeavyRain: {
                    this._currentWeather = Enum.Weather.Raining;
                    break;
                }
                case Raining: {
                    this._currentWeather = p == 0 ? Enum.Weather.Drizzling : Enum.Weather.HeavyRain;
                    break;
                }
                case HeavySnow: {
                    this._currentWeather = Enum.Weather.Snowing;
                    break;
                }
                case Snowing: {
                    this._currentWeather = p == 0 ? Enum.Weather.LightSnow : Enum.Weather.HeavySnow;
                    break;
                }
                case LightSnow: {
                    this._currentWeather = p == 0 ? Enum.Weather.Snowing : Enum.Weather.Cloudy;
                    break;
                }
                case Drizzling: {
                    this._currentWeather = p == 0 ? Enum.Weather.Raining : Enum.Weather.Cloudy;
                    break;
                }
                case Cloudy: {
                    this._currentWeather = this.checkWeather(oldWeather, this._habitats.get(this._currentHabitat));
                }
            }
        }
    }

    private WeatherRecord checkCurrentWeather() {
        this._currentWeather = this.checkWeather(this._currentWeather, this._habitats.get(this._currentHabitat));
        MapLevel map = this._world.getCurrentMap();
        Zone zone = this._world.getCurrentZone();
        return this.addCurrentWeatherToRecord(this.getExistingWeatherRecord(map, zone), map, zone);
    }

    private Enum.Weather checkWeather(Enum.Weather currentWeather, Habitat habitat) {
        Random random = new Random();
        int prob = 0;
        byte seasonMod = 0;
        byte cloudyMod = 0;
        boolean isWeather = false;
        Enum.Season season = this.getSeason();
        if (currentWeather == Enum.Weather.Cloudy) {
            cloudyMod = habitat.getCloudMod();
        }
        switch (season) {
            case Spring: {
                seasonMod = habitat.getSpringMod();
                break;
            }
            case Summer: {
                seasonMod = habitat.getSummerMod();
                break;
            }
            case Fall: {
                seasonMod = habitat.getFallMod();
                break;
            }
            case Winter: {
                seasonMod = habitat.getWinterMod();
            }
        }
        try {
            if (currentWeather == Enum.Weather.Clear || currentWeather == Enum.Weather.Cloudy) {
                prob = random.nextInt(habitat.getWeatherChance()) + (seasonMod + cloudyMod);
                if (prob > habitat.getWeatherChance() - 1) {
                    isWeather = true;
                }
                currentWeather = isWeather && currentWeather == Enum.Weather.Clear ? ((prob = random.nextInt(2)) == 1 ? Enum.Weather.Cloudy : this.calcWeather(currentWeather)) : (isWeather ? this.calcWeather(currentWeather) : ((double)(prob = random.nextInt(habitat.getWeatherChange()) + seasonMod) >= (double)habitat.getWeatherChange() * Config._cloudyCoefficient ? Enum.Weather.Cloudy : Enum.Weather.Clear));
            } else {
                prob = random.nextInt(habitat.getWeatherChange()) - seasonMod;
                currentWeather = this.calcWeather(currentWeather);
                if ((double)prob > (double)habitat.getWeatherChange() * 0.5) {
                    prob = random.nextInt(Config._weatherChangeChance);
                    if (currentWeather == Enum.Weather.Drizzling || currentWeather == Enum.Weather.LightSnow) {
                        if (prob <= 2) {
                            currentWeather = Enum.Weather.Cloudy;
                        } else if (prob == 3) {
                            currentWeather = Enum.Weather.Clear;
                        } else if (prob <= 6) {
                            currentWeather = currentWeather == Enum.Weather.Drizzling ? Enum.Weather.Raining : Enum.Weather.Snowing;
                        }
                    } else if (currentWeather == Enum.Weather.Raining || currentWeather == Enum.Weather.Snowing) {
                        if (prob == 0) {
                            currentWeather = Enum.Weather.Cloudy;
                        } else if (prob <= 4) {
                            currentWeather = currentWeather == Enum.Weather.Raining ? Enum.Weather.Drizzling : Enum.Weather.LightSnow;
                        } else if (prob <= 6) {
                            currentWeather = currentWeather == Enum.Weather.Raining ? Enum.Weather.HeavyRain : Enum.Weather.HeavySnow;
                        }
                    } else if ((currentWeather == Enum.Weather.HeavyRain || currentWeather == Enum.Weather.HeavySnow) && prob < 4) {
                        currentWeather = currentWeather == Enum.Weather.HeavyRain ? Enum.Weather.Raining : Enum.Weather.Snowing;
                    }
                }
            }
        }
        catch (IllegalArgumentException e) {
            currentWeather = Enum.Weather.Clear;
        }
        return currentWeather;
    }

    private Enum.Weather calcWeather(Enum.Weather weather) {
        boolean warm = this._dayTemp > Config._freezingTemp;
        switch (weather) {
            case Snowing: 
            case Raining: {
                if (warm) {
                    return Enum.Weather.Raining;
                }
                return Enum.Weather.Snowing;
            }
            case HeavySnow: 
            case HeavyRain: {
                if (warm) {
                    return Enum.Weather.HeavyRain;
                }
                return Enum.Weather.HeavySnow;
            }
        }
        if (warm) {
            return Enum.Weather.Drizzling;
        }
        return Enum.Weather.LightSnow;
    }

    private WeatherRecord addCurrentWeatherToRecord(WeatherRecord existing, MapLevel map, Zone zone) {
        if (existing != null) {
            existing.setWeather(this._currentWeather);
            existing.setTemp(this._temp);
            existing.setDayTemp(this._dayTemp);
        } else if (this._isHome) {
            existing = new WeatherRecord(this._isHome, this._currentHabitat, this._currentWeather, this._temp, this._dayTemp);
            this._weatherRecord.add(existing);
        } else {
            existing = new WeatherRecord(new int[]{map.getMapNum(), zone.getZoneNum()}, zone.getCurrentLocationBackgroundRange().getRange(), this._currentWeather, this._temp, this._dayTemp, this._currentHabitat);
            this._weatherRecord.add(existing);
        }
        return existing;
    }

    private boolean setCurrentWeatherFromRecord(WeatherRecord existing) {
        if (existing != null) {
            this._currentWeather = existing.getWeather();
            this._temp = existing.getTemp();
            this._dayTemp = existing.getDayTemp();
            return true;
        }
        return false;
    }

    private WeatherRecord getExistingWeatherRecord(MapLevel map, Zone zone) {
        for (WeatherRecord w : this._weatherRecord) {
            if (!(this._isHome ? w.getIsHome() && w.getHabitat() == this._currentHabitat : map != null && w.getMapZone()[0] == map.getMapNum() && zone != null && w.getMapZone()[1] == zone.getZoneNum() && w.getStepsRange()[1] >= zone.getCurrentLocation() && w.getStepsRange()[0] <= zone.getCurrentLocation())) continue;
            return w;
        }
        return null;
    }

    private void randomWeather(int habitat) {
        if (this._currentWeather == Enum.Weather.Clear) {
            this.setDayTemp();
            Random r = new Random();
            int prob = r.nextInt(2);
            Enum.Weather w = this.checkWeather(this._currentWeather, this._habitats.get(habitat));
            if (prob == 0 && (w = this.checkWeather(Enum.Weather.Cloudy, this._habitats.get(habitat))) != Enum.Weather.Clear && w != Enum.Weather.Cloudy) {
                w = this.checkWeather(w, this._habitats.get(habitat));
                prob = r.nextInt(2);
                if (prob == 0) {
                    w = this.checkWeather(w, this._habitats.get(habitat));
                    prob = r.nextInt(2);
                    if (prob == 0) {
                        w = this.checkWeather(w, this._habitats.get(habitat));
                    }
                }
            }
            this._currentWeather = w;
        }
    }

    public void secLapse(byte currentSec) {
        if (this._alive && currentSec != 0 && currentSec % 1 == 0 && this._battleImmunity > 0) {
            --this._battleImmunity;
        }
    }

    public void decEnemyCooldown() {
        for (Enemy e : this._world.getEnemies()) {
            if (e == null) continue;
            e.decCooldown();
        }
    }

    public void checkRestock(byte currentMin) {
        if (currentMin % Config._restockMin == 0 && this._restock < Config._restockMax && Utility.randomChance(Config._restockShopChance, 100)) {
            this._restock = (byte)(this._restock + 1);
        }
    }

    public void checkGiftCall(byte currentMin) {
        if (this._growthStage != Enum.Stage.Egg && currentMin % Config._giftChanceMin == 0 && this._currentState == Enum.State.Idling && this._currentState != Enum.State.GiftCall && this._currentState != Enum.State.Gifting && this._currentState != Enum.State.Dying && this._alive && !this._asleep && this._isHome && this._currentMood == Enum.Mood.Happy && this._growthStage != Enum.Stage.Egg && this._growthStage != Enum.Stage.Fresh && this._growthStage != Enum.Stage.InTraining) {
            this._gift = this.checkGift();
            if (this._gift != null) {
                this.setCurrentState(Enum.State.GiftCall);
            }
        }
    }

    public void checkFilthSick(byte currentMin) {
        if (currentMin % Config._filthSickMin == 0 && this.isFilth()) {
            int filth = this.countFilth();
            this.checkWorseSick(Config._filthWorseSickChance * filth, (int)((double)Config._filthSickChanceBound * this._poopSickBoundMultiplier));
            this.checkSick(Config._filthSickChance * filth, (int)((double)Config._filthSickChanceBound * this._poopSickBoundMultiplier));
        }
    }

    public void checkFilthMoodDec(byte currentMin) {
        if (this._growthStage != Enum.Stage.Egg && currentMin % Config._filthMoodDecMin == 0 && this.isFilth()) {
            this.setMood(this._mood + this._filthLapseMoodChange * this.countFilth());
        }
    }

    public void checkWeakConsumable(byte currentMin) {
        if (currentMin % Config._weakConsummableOffMin == 0) {
            this._useWeakConsumable = false;
        }
    }

    public void checkRefusedOff(byte currentMin) {
        if (currentMin % Config._refusedOffMin == 0 && this._refused && !this._scold) {
            this._refused = false;
            this.setMood(this._mood + Config._refusedOffMoodInc);
            this.setObedience(this._obedience - Config._refusedOffObedienceDec);
        }
    }

    public void checkFatigueLapse(byte currentMin) {
        if (this.isFatigued() && currentMin % Config._fatigueLapseMin == 0) {
            this.setFatigueLength(this._fatigueLength - 1);
        }
    }

    public void checkIncompatibleHabitat(byte currentMin) {
        Habitat h;
        int chance;
        if (this._growthStage != Enum.Stage.Egg && currentMin % Config._incompatibleHabitatMin == 0 && (chance = (this.incompatibleField(this._field, h = this.getCurrentHabitat()) ? Config._incompatibleFieldSickChance : (byte)0) + (this.incompatibleElement(this._element, h) ? Config._incompatibleElementSickChance : (byte)0)) > 0) {
            this.checkWorseSick(chance, Config._incompatibleHabitatBound);
            this.checkSick(chance, Config._incompatibleHabitatBound);
        }
    }

    public void checkNapEnergy(byte currentMin) {
        if (this._growthStage != Enum.Stage.Egg && currentMin % Config._napEnergyMin == 0 && this._nap) {
            this._napEnergyInc = (byte)(this._napEnergyInc + this._awakeLapseInc);
            if (this._napEnergyInc >= Config._napEnergyInc) {
                this.setEnergy((byte)(this._energy + this._napEnergyGain));
                this._napEnergyInc = (byte)(this._napEnergyInc - Config._napEnergyInc);
            }
        }
    }

    public void checkTempRecord(byte currentMin) {
        if (currentMin % Config._recordTempMin == 0) {
            this._tempRecord[0] = this._tempRecord[0] + 1;
            this._tempRecord[1] = this._tempRecord[1] + this._temp;
        }
    }

    public void checkObedienceRecord(byte currentMin) {
        if (currentMin % Config._obedienceRecordMin == 0) {
            this._obedienceRecord[0] = this._obedienceRecord[0] + 1;
            this._obedienceRecord[1] = this._obedienceRecord[1] + this._obedience;
        }
    }

    public void checkItemInterest(byte currentMin) {
        if (this._itemInterest > 0 && currentMin % Config._itemInterestLapseMin == 0) {
            this.setItemInterestLapse(this._itemInterestLapse - 1);
        }
    }

    public void timeToAgeMin(byte currentMin) {
        if (currentMin % Config._timeToAgeMin == 0) {
            this.setTimeToAge(this._timeToAge + 1);
        }
    }

    public void checkMoodRecord(byte currentMin) {
        if (currentMin % Config._moodRecordMin == 0) {
            int n = this.getCurrentMood().ordinal();
            this._moodRecord[n] = this._moodRecord[n] + 1;
            int n2 = this.getCurrentMood().ordinal();
            this._dailyMoodRecord[n2] = this._dailyMoodRecord[n2] + 1;
        }
        if ((this.getCurrentMood() == Enum.Mood.Unhappy || this.getCurrentMood() == Enum.Mood.Depressed) && currentMin % Config._timeRankDecreaseUnhappyMin == 0) {
            this._timeRanks.decRankAndCheckFavDislikeChange(this.checkTime(this._clock.getHours()), Config._rankChangeUnhappy);
        }
    }

    public void checkHabitatRecord(byte currentMin) {
        if (currentMin % Config._habitatRecordMin == 0) {
            int n = this._currentHabitat;
            this._habitatRecord[n] = this._habitatRecord[n] + 1;
        }
    }

    public void checkWeightRecord(byte currentMin) {
        if (currentMin % Config._weightRecordMin == 0) {
            int n = this._overweight.ordinal();
            this._weightRecord[n] = this._weightRecord[n] + 1;
        }
    }

    public MinLapsePacket minLapse(byte currentMin) {
        MinLapsePacket f = null;
        if (this._alive) {
            this.decEnemyCooldown();
            if (currentMin == 0) {
                currentMin = (byte)60;
            }
            if (currentMin != 0) {
                this.checkRestock(currentMin);
                this.checkAllWeather(currentMin);
                this.checkEveryTemp(currentMin);
                this.personalityTracker(currentMin);
                this.xAntibodyCountChange(currentMin);
                this.checkGiftCall(currentMin);
                this.checkPraiseScoldWindow(currentMin);
                this.checkRecoveryTime(currentMin);
                this.checkCallMinutes(currentMin);
                this.checkFilthSick(currentMin);
                this.checkFilthMoodDec(currentMin);
                this.checkWeakConsumable(currentMin);
                this.checkRefusedOff(currentMin);
                this.toNapSleepLapse(currentMin);
                this.vitaminLapse(currentMin);
                this.bandageLapse(currentMin);
                this.medLapse(currentMin);
                this.checkFatigueLapse(currentMin);
                this.checkIdealTempMoodChange(currentMin);
                this.checkIncompatibleHabitat(currentMin);
                this.checkBadTempSick(currentMin);
                this.checkNapEnergy(currentMin);
                this.checkTempRecord(currentMin);
                this.checkObedienceRecord(currentMin);
                this.checkItemInterest(currentMin);
                this.moodLapse(currentMin);
                this.enthusiasmLapse(currentMin);
                this.checkDepressed(currentMin);
                this.obedienceLapse(currentMin);
                this.sickLapse(currentMin);
                this.injuryLapse(currentMin);
                this.bmLapse(currentMin);
                this.poopWaitMoodCheck(currentMin);
                this.timeToAgeMin(currentMin);
                this.checkDisciplineCall(currentMin);
                this.checkMoodRecord(currentMin);
                this.checkHabitatRecord(currentMin);
                this.checkWeightRecord(currentMin);
                f = this.checkAutoCare(currentMin);
                this.sleepDecay(currentMin);
            }
            this.checkConsumableEffect();
            this.checkNeedDecay();
            this.autoSave();
        }
        return f;
    }

    private MinLapsePacket checkAutoCare(int currentMin) {
        boolean cleaned = false;
        FoodType f = null;
        boolean lightSwitch = false;
        if (this._autoCare && currentMin % Config._autoCarePaymentMin == 0 && this._isHome) {
            int price = 0;
            switch (this._growthStage) {
                case Egg: {
                    price = Config._autoCareStageIHourPrice;
                    break;
                }
                case Fresh: {
                    price = Config._autoCareStageIHourPrice;
                    break;
                }
                case InTraining: {
                    price = Config._autoCareStageIIHourPrice;
                    break;
                }
                case Rookie: {
                    price = Config._autoCareStageIIIHourPrice;
                    break;
                }
                case Champion: {
                    price = Config._autoCareStageIVHourPrice;
                    break;
                }
                case Ultimate: {
                    price = Config._autoCareStageVHourPrice;
                    break;
                }
                case Mega: {
                    price = Config._autoCareStageVIHourPrice;
                }
            }
            if (this._bits >= price) {
                this.setBits(this._bits - price);
            } else {
                this._autoCare = false;
            }
        }
        if (this._autoCare && currentMin % Config._autoCareCheckMin == 0 && !Utility.containsState(Utility.ASSISTANT_ANIM, this._currentState) && !Utility.containsState(Utility.ASSISTANT_ANIM, this._animQueue) && Utility.containsState(Utility.ENABLE_DURING_STATE, this._currentState)) {
            if (!this._asleep) {
                if (this.isFilth() && this.doAutoCare()) {
                    cleaned = true;
                } else if (this._hunger == 0 && this.doAutoCare()) {
                    f = this.getFoodByID(Config._autoCareHungerFoodID);
                } else if (this._exercise == 0 && this.doAutoCare()) {
                    f = this.getFoodByID(Config._autoCareStrengthFoodID);
                }
            } else if (this.isFilth() && this.doAutoCare()) {
                cleaned = true;
            } else if (this._lights && !this.isFuton() && this.doAutoCare()) {
                lightSwitch = true;
            }
        }
        return new MinLapsePacket(cleaned, f, lightSwitch);
    }

    public boolean isFuton() {
        return this._careEffects.get(this._items.get(81).getEffectID()).isActive();
    }

    public void checkConsumableEffect() {
        if (this._growthStage != Enum.Stage.Egg) {
            for (CareEffect e : this._careEffects) {
                if (!e.isActive()) continue;
                int min = e.getLapse();
                this.setMood(this._mood + this.getConsumableEffectChange(e.getMoodChange(), min));
                this.setEnergy((byte)(this._energy + this.getConsumableEffectChange(e.getEnergyChange(), min)));
                this.setHunger((byte)(this._hunger + this.getConsumableEffectChange(e.getHungerChange(), min)));
                this.setExercise((byte)(this._exercise + this.getConsumableEffectChange(e.getStrengthChange(), min)));
                this.setSleepLapse(this._sleepLapse + this.getConsumableEffectChange(e.getSleepLapseChange(), min));
                this.setAwakeLapse(this._awakeLapse + this.getConsumableEffectChange(e.getAwakeLapseChange(), min));
                e.decLapse();
            }
        }
    }

    private int getConsumableEffectChange(int[] change, int min) {
        if (change[1] > 0 && change[1] % min == 0) {
            return change[0];
        }
        return 0;
    }

    public void checkNeedDecay() {
        if (this._growthStage != Enum.Stage.Egg) {
            this._hungerDecayLapse = (byte)(this._hungerDecayLapse - 1);
            Random ran = new Random();
            int r = ran.nextInt(Config._lessHungerChance) + this._glutton * Config._hungerDecayGluttonCoefficient;
            if (r < 0) {
                this._hungerDecayLapse = (byte)(this._hungerDecayLapse + 1);
            } else if (r >= Config._lessHungerChance) {
                this._hungerDecayLapse = (byte)(this._hungerDecayLapse - 1);
            }
            if (this._asleep && this._hunger > Config._sleepMinHungerDecay) {
                this._hungerDecayLapse = (byte)(this._hungerDecayLapse - (this._hunger - Config._sleepMinHungerDecay));
            }
            if (this._hungerDecayLapse <= 0) {
                this.calcHungerDecayLapse();
                this.hungerDecay();
            }
            this._strengthDecayLapse = (byte)(this._strengthDecayLapse - 1);
            r = ran.nextInt(Config._lessStrengthChance) + this._restless * Config._strengthDecayRestlessCoefficient;
            if (r < 0) {
                this._strengthDecayLapse = (byte)(this._strengthDecayLapse + 1);
            } else if (r >= Config._lessStrengthChance) {
                this._strengthDecayLapse = (byte)(this._strengthDecayLapse - 1);
            }
            if (this._asleep && this._exercise > Config._sleepMinStrengthDecay) {
                this._strengthDecayLapse = (byte)(this._strengthDecayLapse - (this._exercise - Config._sleepMinStrengthDecay));
            }
            if (this._strengthDecayLapse <= 0) {
                this.calcStrengthDecayLapse();
                this.exerciseDecay();
            }
        }
    }

    public void calcHungerDecayLapse() {
        int min = this.calcNeedDecay(this._hungerDecayCoefficient);
        this._hungerDecayLapse = (byte)Utility.calcVariance(Config._hungerDecayVariance, min);
        this._minToDecayHunger = this._hungerDecayLapse;
    }

    public void calcStrengthDecayLapse() {
        int min = this.calcNeedDecay(this._strengthDecayCoefficient);
        this._strengthDecayLapse = (byte)Utility.calcVariance(Config._strengthDecayVariance, min);
        this._minToDecayStrength = this._strengthDecayLapse;
    }

    private int calcNeedDecay(double decay) {
        double b = decay;
        double a = Config._needDecayExponent;
        int min = (int)Math.ceil(b * Math.pow(Math.E, -a * (double)(this._lapsedLife - this._growthPeriod)));
        if ((double)min > b) {
            min = (int)b;
        }
        return min;
    }

    public void checkPraiseScoldWindow(byte currentMin) {
        if (currentMin % Config._praiseScoldWindowCheckMin == 0) {
            if (this._praise) {
                this.setPraiseWindow((byte)(this._praiseWindow + 1));
            }
            if (this._scold) {
                this.setScoldWindow((byte)(this._scoldWindow + 1));
            }
        }
    }

    public void checkCallMinutes(byte currentMin) {
        if (currentMin % Config._callMinutesCheckMin == 0 && (this.checkCall() || this._disciplineCall)) {
            this.setMood(this._mood - Config._callMoodDec);
            this.incCallMinutes();
        }
    }

    public void checkEveryTemp(byte currentMin) {
        if ((currentMin % Config._weatherTempMin == 0 && this._currentWeather != Enum.Weather.Clear && this._currentWeather != Enum.Weather.Cloudy || currentMin % Config._tempLapseMin == 0) && !this.pauseTemp()) {
            this._temp = (byte)this.checkTemp(this._temp, this._dayTemp, this.getCurrentHabitat());
            for (WeatherRecord w : this._weatherRecord) {
                w.setTemp(this.checkTemp(w.getTemp(), w.getDayTemp(), this._habitats.get(w.getHabitat())));
            }
        }
    }

    public int getAdjustedDayTemp(int dayTemp, Habitat habitat) {
        byte minusWeather = 0;
        switch (this._currentWeather) {
            case Snowing: 
            case HeavyRain: {
                minusWeather = Config._snowingHeavyRainTempFactor;
                break;
            }
            case Cloudy: {
                minusWeather = Config._cloudyTempFactor;
                break;
            }
            case Drizzling: {
                minusWeather = Config._drizzlingTempFactor;
                break;
            }
            case LightSnow: 
            case Raining: {
                minusWeather = Config._lightSnowRainingTempFactor;
                break;
            }
            case HeavySnow: {
                minusWeather = Config._heavySnowFactor;
            }
        }
        dayTemp -= minusWeather;
        Enum.Time currentTime = this.checkTime(this._clock.getHours());
        if ((dayTemp -= currentTime == Enum.Time.Night ? habitat.getNightTempFactor() : (currentTime == Enum.Time.Morning ? habitat.getMorningTempFactor() : 0)) < 0) {
            dayTemp = 0;
        }
        return dayTemp;
    }

    private int checkTemp(int temp, int dayTemp, Habitat habitat) {
        if (this._tempGoal > Config._maxTemp) {
            if (temp > (dayTemp = this.getAdjustedDayTemp(dayTemp, habitat)) && temp - 1 >= 0) {
                --temp;
            } else if (temp < dayTemp && temp + 1 <= Config._maxTemp) {
                ++temp;
            }
        } else if (temp > this._tempGoal && temp - 1 >= 0) {
            --temp;
        } else if (temp < this._tempGoal && temp + 1 <= Config._maxTemp) {
            ++temp;
        } else {
            this._tempGoal = (byte)(Config._maxTemp + 1);
        }
        if (this.isSick()) {
            Random r = new Random();
            int i = r.nextInt(Config._sickTempDecChance);
            if (i == 1) {
                temp = temp - Config._sickTempDec < 0 ? 0 : (temp -= Config._sickTempDec);
            } else if (i == 2) {
                temp = temp + Config._sickTempInc > Config._maxTemp ? (int)Config._maxTemp : (temp += Config._sickTempInc);
            }
        }
        return temp;
    }

    public boolean pauseTemp() {
        boolean pause = false;
        for (CareEffect e : this._careEffects) {
            if (!e.isActive() || !e.pauseTemp()) continue;
            pause = true;
            break;
        }
        return pause;
    }

    public Enum.Mood checkIdealTemp() {
        Enum.Mood mood = Enum.Mood.Neutral;
        mood = this._temp >= this._idealTemp[0] && this._temp <= this._idealTemp[1] ? Enum.Mood.Happy : (this.tempTooHigh() || this.tempTooLow() ? Enum.Mood.Unhappy : Enum.Mood.Neutral);
        return mood;
    }

    public boolean tempTooHigh() {
        return this._temp >= this._idealTemp[1] + Config._upperIdealTemp;
    }

    public boolean tempTooLow() {
        return this._temp <= this._idealTemp[0] - Config._lowerIdealTemp;
    }

    public boolean compatibleField(Enum.Field f, Habitat h) {
        return h != null ? h.getCompatibleFields().contains((Object)f) : false;
    }

    public boolean incompatibleField(Enum.Field f, Habitat h) {
        return h != null ? h.getIncompatibleFields().contains((Object)f) : false;
    }

    public boolean compatibleElement(Enum.Element e, Habitat h) {
        return h != null ? h.getCompatibleElements().contains((Object)e) : false;
    }

    public boolean incompatibleElement(Enum.Element e, Habitat h) {
        return h != null ? h.getIncompatibleElements().contains((Object)e) : false;
    }

    private void checkIdealTempMoodChange(byte currentMin) {
        if (this._growthStage != Enum.Stage.Egg && currentMin % Config._idealTempMoodMin == 0) {
            Enum.Mood mood = this.checkIdealTemp();
            Habitat h = this.getCurrentHabitat();
            int change = (this.compatibleElement(this._element, h) ? Config._compatibleElementMoodChange : (byte)0) + (this.compatibleField(this._field, h) ? Config._compatibleFieldMoodChange : (byte)0) + (this.incompatibleField(this._field, h) ? Config._incompatibleFieldMoodChange : (byte)0) + (this.incompatibleElement(this._element, h) ? Config._incompatibleElementMoodChange : (byte)0);
            if (mood == Enum.Mood.Happy) {
                this.setMood(this.getMood() + Config._idealTempInc + change);
            } else if (mood == Enum.Mood.Unhappy) {
                this.setMood(this.getMood() - Config._idealTempDec + change);
            }
        }
    }

    private void checkBadTempSick(byte currentMin) {
        Enum.Mood mood;
        if (this._growthStage != Enum.Stage.Egg && currentMin % Config._badTempSickMin == 0 && (mood = this.checkIdealTemp()) == Enum.Mood.Unhappy) {
            this.checkWorseSick(Config._sickChanceBadTemp, Config._badTempSickChanceBound);
            this.checkSick(Config._sickChanceBadTemp, Config._badTempSickChanceBound);
        }
    }

    private void moodLapse(byte currentMin) {
        if (!(this._growthStage == Enum.Stage.Egg || currentMin % Config._moodLapseMin != 0 || this._asleep && this._mood <= Config._minMoodAsleep || this.isSick() || this.isInj() || this.checkCall())) {
            if (this._hunger <= Config._fullHunger / 2) {
                if (this._glutton == 1) {
                    this._mood += Config._gluttonLowHungerMoodChange;
                } else if (this._glutton == -1) {
                    this._mood += Config._notGluttonLowHungerMoodChange;
                }
            } else if (this._hunger > Config._fullHunger) {
                if (this._glutton == 1) {
                    this._mood += Config._gluttonHighHungerMoodChange;
                } else if (this._glutton == -1) {
                    this._mood += Config._notGluttonHighHungerMoodChange;
                }
            }
            if (this._restless <= Config._fullStrength / 2) {
                if (this._restless == 1) {
                    this._mood += Config._restlessLowStrengthMoodChange;
                } else if (this._restless == -1) {
                    this._mood += Config._notRestlessLowStrengthMoodChange;
                }
            } else if (this._restless > Config._fullStrength) {
                if (this._restless == 1) {
                    this._mood += Config._restlessHighStrengthMoodChange;
                } else if (this._restless == -1) {
                    this._mood += Config._notRestlessHighStrengthMoodChange;
                }
            }
            if (this._currentMood == Enum.Mood.Happy) {
                this.setMood(this._mood - Config._happyMoodLapseDec);
            } else if (this._currentMood == Enum.Mood.Unhappy) {
                if (this._mood > Config._minMood / 2) {
                    this.setMood(this._mood + Config._unhappyMoodLapseInc);
                } else if (this._mood < Config._minMood / 2) {
                    this.setMood(this._mood + Config._veryUnhappyMoodLapseInc);
                }
            } else if (this._currentMood == Enum.Mood.Neutral) {
                if (this._mood < Config._maxMood / 2 && this._mood >= Config._veryNeutralMoodLapseDec) {
                    this.setMood(this._mood - Config._veryNeutralMoodLapseDec);
                } else {
                    this.setMood(this._mood - Config._neutralMoodLapseDec);
                }
            }
            if (this._overweight != Enum.Weight.Healthy) {
                this.setMood(this._mood - Config._badWeightMoodLapseDec);
            }
        }
    }

    public synchronized void writeVars(JTextArea area1, JTextArea area2, Enum.Menu currentMenu) {
        area1.setText("");
        area1.append("MornT | DayT | NghtT: " + this._morningTrain + " | " + this._dayTrain + " | " + this._nightTrain + "\n");
        area1.append("P | M | V: " + this._protein + " | " + this._mineral + " | " + this._vitamin + "\n");
        area1.append("CurrentState: " + (Object)((Object)this._currentState) + "\n");
        area1.append("CurrentMenu: " + (Object)((Object)currentMenu) + "\n");
        area1.append("Wthr: " + (Object)((Object)this._currentWeather) + " | TmpAvg: " + this._tempRecord[1] / (this._tempRecord[0] == 0 ? 1 : this._tempRecord[0]) + "\n");
        area1.append("Bonus: " + this._bonus + " | Generation: " + this._generationHistory.size() + "\n");
        area1.append("Day's Mood: H" + this._dailyMoodRecord[0] + ", N" + this._dailyMoodRecord[1] + ", U" + this._dailyMoodRecord[2] + ", D" + this._dailyMoodRecord[3] + "\n");
        area1.append("TimeToAge: " + this._timeToAge + " | Day: " + this._day + "\n");
        area1.append("Call H: " + this._callMinutesHunger + " | S: " + this._callMinutesStrength + " | L: " + this._callMinutesLights + " | P: " + this._callMinutesPoop + " | D: " + this._callMinutesDiscipline + "\n");
        area1.append("CareMistake: " + this._mistake + " | Missed Day: " + this._mistakeDay + "\n");
        area1.append("Disturb: " + this._disturb + " | Overeat: " + this._overeat + "\n");
        area1.append("Filth: " + this.countFilth() + " | BMGauge: " + this._bmGauge + "\n");
        area1.append("Game Modified: " + this._gameModified + "\n");
        area1.append("Checksum: " + this._checksum + "\n");
        area1.append("BattleImmunity: " + this._battleImmunity + "\n");
        area1.append("Habitat: " + this.getCurrentHabitat().getName() + "\n");
        area1.append("MajorHabitat: " + (this.getMajorHabitat() > -1 ? this._habitats.get(this.getMajorHabitat()).getName() : "None") + "\n");
        area1.append("Praise: " + this._praise + " | PraiseWindow: " + this._praiseWindow + "\n");
        area1.append("Scold: " + this._scold + " | ScoldWindow: " + this._scoldWindow + "\n");
        area1.append("Refused: " + this._refused + "\n");
        area1.append("Compliance: " + this._compliance + "\n");
        area1.append("Mood: " + this._mood + "\n");
        area1.append("CurrentMood: " + (Object)((Object)this._currentMood) + "\n");
        area1.append("Enthusiasm: " + this._enthusiasm + "\n");
        area1.append("Obedience: " + this._obedience + "\n");
        area1.append("Hunger: " + this._hunger + " | Exercise: " + this._exercise + "\n");
        area1.append("ItemDisinterest: " + this._itemInterest + "\n");
        area1.append("Energy: " + this._energy + "\n");
        area1.append("BaseWeight: " + this._baseWeight + "\n");
        area1.append("Calories: " + this._calories + "\n");
        area1.append("Max | Min Calories: " + this.getMaxCalories() + " | " + this.getMinCalories() + "\n");
        area1.append("Stomach Capacity: " + this._stomachCapacity + "\n");
        area1.append("DayTemp: " + this.getAdjustedDayTemp(this._dayTemp, this.getCurrentHabitat()) + "\n");
        area1.append("CanEvolve/Die: " + this._canEvolveOrDie + "\n");
        area1.append("PostponeEvolve/Die: " + (this._postponeEvolve ? "T" : "F") + "/" + (this._postponeDie ? "T" : "F") + "\n");
        area1.append("HealthPoints: " + this._fullHealthPoints + "\n");
        area1.append("PerfectWins: " + this._perfectWins + "\n");
        if (this._world.getCurrentMap() != null) {
            area1.append("Map: " + this._world.getCurrentMap().getMapNum() + "\n");
        }
        if (this._world.getCurrentZone() != null) {
            area1.append("Total Steps: " + this._world.getCurrentZone().getTotalSteps() + "\n");
        }
        area1.append("EnergyDec: " + this._world.getEnergyDec() + "\n");
        area1.append("WildBattleWait: " + this._world.getWildBattleWait() + "\n");
        area1.append("MoodRecord: H" + this._moodRecord[0] + ", N" + this._moodRecord[1] + ", U" + this._moodRecord[2] + ", D" + this._moodRecord[3] + "\n");
        area1.append("WeightRecord: O" + this._weightRecord[0] + ", N" + this._weightRecord[1] + ", U" + this._weightRecord[2] + "\n");
        area1.append("ObedienceAverage: " + this._obedienceRecord[1] / (this._obedienceRecord[0] == 0 ? 1 : this._obedienceRecord[0]) + "\n");
        area1.append("MajorFood: " + this.getMajorFood().toString() + "\n");
        area1.append("XAntibodyCount: " + this._xAntibodyCount);
        area2.setText("");
        area2.append("Restless: " + this._restless + "\n");
        area2.append("Glutton: " + this._glutton + "\n");
        area2.append("Disposition: " + this._disposition + "\n");
        area2.append("TotalLifespan: " + this._totalLifespan + "\n");
        area2.append("LapsedLife: " + this._lapsedLife + "\n");
        area2.append("GrowthStage: " + (Object)((Object)this._growthStage) + "\n");
        area2.append("GrowthPeriod: " + this._growthPeriod + "\n");
        area2.append("LastHungerDecayMin: " + this._hungerDecayLapse + "\n");
        area2.append("LastStrengthDecayMin: " + this._strengthDecayLapse + "\n");
        area2.append("DisciplineCall: " + this._disciplineCall + "\n");
        area2.append("Injured: " + this.isInj() + " | Length: " + this._injLength + "\n");
        area2.append("Sick: " + this.isSick() + " | Length: " + this._sickLength + "\n");
        area2.append("SickCount: " + this._sickCount + " | InjCount: " + this._injCount + "\n");
        area2.append("VitaminLapse: " + this._vitaminLapse + "\n");
        area2.append("BandageLapse: " + this._bandageLapse + "\n");
        area2.append("Asleep: " + this._asleep + " | Nap: " + this._nap + "\n");
        area2.append("MedLapse: " + this._medLapse + "\n");
        area2.append("Fatigued: " + this.isFatigued() + " | Length: " + this._fatigueLength + "\n");
        area2.append("SleepMin: " + this._sleepMinutes + " | NapMin: " + this._napEnergyInc + "\n");
        area2.append("SLapse: " + this._sleepLapse + " | SLimit: " + this._sleepLimit + "\n");
        area2.append("ALapse: " + this._awakeLapse + " | ALimit: " + this._awakeLimit + "\n");
        if (this._foodRanks != null) {
            area2.append("MeatRank: " + this._foodRanks.getRank(Enum.Food.Meat).getRank() + "\n");
            area2.append("VegRank: " + this._foodRanks.getRank(Enum.Food.Veg).getRank() + "\n");
            area2.append("FishRank: " + this._foodRanks.getRank(Enum.Food.Fish).getRank() + "\n");
            area2.append("FruitRank: " + this._foodRanks.getRank(Enum.Food.Fruit).getRank() + "\n");
            area2.append("MedRank: " + this._foodRanks.getRank(Enum.Food.Med).getRank() + "\n");
            area2.append("JunkRank: " + this._foodRanks.getRank(Enum.Food.Junk).getRank() + "\n");
            area2.append("GrainRank: " + this._foodRanks.getRank(Enum.Food.Grain).getRank() + "\n");
            area2.append("DairyRank: " + this._foodRanks.getRank(Enum.Food.Dairy).getRank() + "\n");
            area2.append("NoneFoodRank: " + this._foodRanks.getRank(Enum.Food.None).getRank() + "\n");
        }
        if (this._attributeRanks != null) {
            area2.append("VaccineRank: " + this._attributeRanks.getRank(Enum.Attribute.Vaccine).getRank() + "\n");
            area2.append("DataRank: " + this._attributeRanks.getRank(Enum.Attribute.Data).getRank() + "\n");
            area2.append("VirusRank: " + this._attributeRanks.getRank(Enum.Attribute.Virus).getRank() + "\n");
            area2.append("NoneAttributeRank: " + this._attributeRanks.getRank(Enum.Attribute.None).getRank() + "\n");
        }
        if (this._timeRanks != null) {
            area2.append("MorningRank: " + this._timeRanks.getRank(Enum.Time.Morning).getRank() + "\n");
            area2.append("NoonRank: " + this._timeRanks.getRank(Enum.Time.Noon).getRank() + "\n");
            area2.append("NightRank: " + this._timeRanks.getRank(Enum.Time.Night).getRank() + "\n");
            area2.append("NoneTimeRank: " + this._timeRanks.getRank(Enum.Time.None).getRank() + "\n");
        }
        area2.append("MoodRank: " + this._moodRank + "\n");
        area2.append("WeightRank: " + this._weightRank + "\n");
        area2.append("EnergyRank: " + this._energyRank + "\n");
        area2.append("HP: " + this._healthPoints + "/" + this._fullHealthPoints + "\n");
        if (this._world.getCurrentZone() != null) {
            area2.append("Zone: " + this._world.getCurrentZone().getZoneNum() + "\n");
            area2.append("Current Steps: " + this._world.getCurrentZone().getCurrentLocation() + "\n");
        }
        area2.append("StepInc: " + this._world.getStepInc() + "\n");
        area2.append("XAntibodyState: " + this._xAntibodyState.toString());
    }

    public int getLevel(int vaccine, int data, int virus, int health) {
        int level = (int)(((double)(vaccine + data + virus) + (double)(health - Config._startingHealthLevel) * (double)Config._healthLevelCoefficient) / (double)Config._levelCoefficient);
        return level <= 0 ? 1 : level;
    }

    public int getDigimonLevel() {
        return this.getLevel(this._vaccinePower, this._dataPower, this._virusPower, this._fullHealthPoints);
    }

    public void checkRecoveryTime(byte currentMin) {
        if (currentMin % Config._recoveryTimeMin == 0 && Utility.containsState(Utility.ENABLE_DURING_STATE, this._currentState) && !this.isFullyRecovered()) {
            this.setHealthPoints(this._healthPoints + (int)((double)this._fullHealthPoints * Config._healthRecoveredCoefficient));
        }
    }

    public boolean canModeChange() {
        return this._evolution.canModeChange(this.getIndex());
    }

    public void modeChange() {
        this.disturb();
        this.checkRefused(null, null, true, Config._modeChangeEnergyChange);
        this.checkCompliant();
        if (!this._refused) {
            if (this._evolution.getDigimon(this._index).getSpecialEvol() == Enum.SpecialEvolution.Mode) {
                if (this._evolution.revert(this, this._evolution.getDigimon(this._index).getPreEvolutions().get(0).getIndex())) {
                    this.setEnergy((byte)(this._energy + Config._modeChangeEnergyChange));
                    this.setCurrentState(Enum.State.Evolving);
                } else {
                    this.setCurrentState(Enum.State.Jeering);
                }
            } else {
                boolean b = this.evol(false, true);
                if (!b) {
                    this.setCurrentState(Enum.State.Jeering);
                } else {
                    this.setEnergy((byte)(this._energy + Config._modeChangeEnergyChange));
                }
            }
        } else {
            this.setCurrentState(Enum.State.Refusing);
        }
    }

    public boolean evol(boolean dying, boolean modeChange) {
        if (this._growthStage == Enum.Stage.Egg) {
            this.setCurrentState(Enum.State.Hatching);
            return true;
        }
        if (this._evolution.canEvolve(this)) {
            if (this.checkEvol(-1, -1, dying, modeChange)) {
                if (!(this._growthStage != Enum.Stage.Egg && this._growthStage != Enum.Stage.Fresh && this._growthStage != Enum.Stage.InTraining || this._isHome)) {
                    this.setCurrentState(Enum.State.Teleport_Leave);
                }
                this.setCurrentState(Enum.State.Evolving);
                return true;
            }
            return false;
        }
        return false;
    }

    public void checkUnlockItem() {
        if (this._unlockConsumable >= 0) {
            this._items.get(this._unlockConsumable).unlockItem(this);
        }
    }

    public boolean checkEvol(int item, int food, boolean dying, boolean modeChange) {
        return this.checkEvol(item, food, dying, modeChange, 0);
    }

    public boolean checkEvol(int item, int food, boolean dying, boolean modeChange, int probChange) {
        boolean evolved = false;
        if (this._evolution.evolve(this, item, food, dying, modeChange, probChange)) {
            evolved = true;
        }
        return evolved;
    }

    public void attributeEvolChange(EvolutionInfo evol, boolean revert) {
        this._vaccinePower += revert ? -evol.getVaccineChange() : evol.getVaccineChange();
        this._dataPower += revert ? -evol.getDataChange() : evol.getDataChange();
        this._virusPower += revert ? -evol.getVirusChange() : evol.getVirusChange();
    }

    public void replaceEvolHistory(int oldIndex, int newIndex) {
        for (int i = 0; i < this._evolHistory.size(); ++i) {
            int j = this._evolHistory.get(i)[1];
            if (this._evolHistory.get(i)[0] != oldIndex) continue;
            int[] a = new int[]{newIndex, j};
            this._evolHistory.set(i, a);
            break;
        }
    }

    public String checkJogress() {
        String evolution = this._evolution.jogress(this);
        return evolution;
    }

    public void jogress(String jogressMatch, int partner) {
        double energy = (double)this._energy + Math.ceil(Config._jogressEnergyChange * (double)this._maxEnergy);
        this._evolution.jogress(jogressMatch, this, this._evolution.getDigimon(this._index), this._evolution.getEvolDigimon(), partner);
        this.setEnergy((byte)energy);
    }

    public void resetEvolVar() {
        this._postponeDie = false;
        this._postponeEvolve = false;
        this._mistake = 0;
        this._overeat = 0;
        this._disturb = 0;
        this._dayTrain = 0;
        this._morningTrain = 0;
        this._nightTrain = 0;
        this._meatEaten = 0;
        this._vegEaten = 0;
        this._fruitEaten = 0;
        this._fishEaten = 0;
        this._junkEaten = 0;
        this._medEaten = 0;
        this._grainEaten = 0;
        this._dairyEaten = 0;
        this._levelsFought.clear();
        this._savedFromDeath = 0;
        this.setSickLength(0);
        this.setInjLength(0);
        this.setFatigueLength(0);
        this.setHealthPoints(this._fullHealthPoints);
        this._dna.resetDNA();
        this.resetRecords();
    }

    private void resetRecords() {
        int i;
        for (i = 0; i < this._moodRecord.length; ++i) {
            this._moodRecord[i] = 0;
        }
        for (i = 0; i < this._habitatRecord.length; ++i) {
            this._habitatRecord[i] = 0;
        }
        for (i = 0; i < this._weightRecord.length; ++i) {
            this._weightRecord[i] = 0;
        }
        this._tempRecord[0] = 0;
        this._tempRecord[1] = 0;
        this._obedienceRecord[0] = 0;
        this._obedienceRecord[1] = 0;
    }

    private void checkFilthyPersonality() {
        if (this.isFilthyEvol()) {
            this._disposition = 1;
            this._glutton = 1;
            this._restless = (byte)-1;
            this._personality = this.checkPersonality();
        }
    }

    public boolean isFilthyEvol() {
        boolean isFilthy = false;
        EvolutionInfo evol = this._evolution.getDigimon(this._index);
        if (evol != null) {
            isFilthy = evol.getSpecialEvol() == Enum.SpecialEvolution.Failed;
        }
        return isFilthy;
    }

    private void checkOverweight() {
        this._overweight = (long)this._weight > (long)this._baseWeight + Math.round((double)this._baseWeight * Config._weightThresh) ? Enum.Weight.Over : ((long)this._weight < (long)this._baseWeight - Math.round((double)this._baseWeight * Config._weightThresh) ? Enum.Weight.Under : Enum.Weight.Healthy);
    }

    private void weightLimitPenalty() {
        this.setMood(this._mood - Config._weightLimitMoodPenalty);
        this.setObedience(this._obedience - Config._weightLimitObediencePenalty);
        this.setEnthusiasm((byte)(this._enthusiasm - Config._weightLimitEnthusiasmPenalty));
    }

    private boolean pauseCall() {
        boolean pause = false;
        for (CareEffect c : this._careEffects) {
            if (!c.isActive() || !c.pauseCall()) continue;
            pause = true;
            break;
        }
        return pause;
    }

    private boolean callMinutesActive() {
        return this.hungerCall() && this._callMinutesHunger >= 0 || this.strengthCall() && this._callMinutesStrength >= 0 || this._callMinutesLights >= 0 && this.lightsCall() || this._callMinutesPoop >= 0 && this.poopCall();
    }

    public boolean checkCall() {
        boolean currentCall = this.callMinutesActive();
        if (currentCall) {
            boolean bl = currentCall = !this.pauseCall();
        }
        if (currentCall) {
            if (this._clock.canResetClockSpeed() && Config._enableFastForward && Config._resetClockSpeedOnCall) {
                this._clock.setFastMod(1);
            }
            if (this._disciplineCall) {
                this._scold = false;
                this._scoldWindow = 0;
                this._callMinutesDiscipline = 0;
            }
            this._disciplineCall = false;
        } else if (!this._disciplineCall) {
            this._clock.setCanResetClockSpeed(true);
            if (!Utility.containsState(Utility.DISABLE_CLOCK_SPEED_CHANGE, this._currentState)) {
                this._clock.clockSpeedToPlayerSetting();
            }
        }
        return currentCall;
    }

    private void hungerMistakePenalty() {
        this.setTotalLifespan(this._totalLifespan - (long)(Config._mistakeHungerLifeDec * this._mistake));
        this.setObedience(this._obedience + this._glutton == 1 ? Config._hungerMistakeObedienceChangeGlutton : Config._hungerMistakeObedienceChange);
        if (Config._enableLifePenaltyAnim) {
            this.setStateNoRepeat(Enum.State.Bad_Health_Jeering);
        }
    }

    private void strengthMistakePenalty() {
        this.setObedience(this._obedience - Config._mistakeStrengthObedienceDec);
    }

    public boolean callMinutesLessThan(int i) {
        return this.poopCall() && this._callMinutesPoop >= 0 && this._callMinutesPoop < i || this.hungerCall() && this._callMinutesHunger >= 0 && this._callMinutesHunger < i || this.strengthCall() && this._callMinutesStrength >= 0 && this._callMinutesStrength < i || this.lightsCall() && this._callMinutesLights >= 0 && this._callMinutesLights < i || this.disciplineCall() && this._callMinutesDiscipline >= 0 && this._callMinutesDiscipline < i;
    }

    private void incMistake() {
        if (this._currentMood == Enum.Mood.Happy) {
            this.setMood(Config._mistakeHappyMoodChange);
        } else {
            this.setMood(this._mood - Config._mistakeMoodDec);
        }
        ++this._mistake;
        this._mistakeDay += Config._mistakeIncMistakeDayChange;
        if (this.poopCall()) {
            this.checkWorseSick(Config._mistakeFilthWorseSickChance);
            this.checkSick(Config._mistakeFilthSickChance);
        } else if (this.isFilth()) {
            int moodMod = this._currentMood != Enum.Mood.Happy && this._currentMood != Enum.Mood.Neutral ? (int)Math.abs(Math.ceil((double)this._mood * Config._mistakeFilthSickChanceMoodCoefficient)) : 0;
            int filth = this.countFilth();
            this.checkWorseSick(Config._mistakeLowFilthWorseSickChance * filth + moodMod);
            this.checkSick(Config._mistakeLowFilthSickChance * filth + moodMod);
        }
        if (this.isFatigued()) {
            this.checkWorseSick(Config._anyMistakeFatiguedWorseSickChance);
            this.checkSick(Config._anyMistakeFatiguedSickChance);
        }
        this.autoSave();
    }

    private void checkDirtyEating(ArrayList<Enum.Food> list, boolean complied) {
        if (this.isFilth()) {
            this.setMood(this._mood - Config._dirtyEatingMoodDec);
            int filth = this.countFilth();
            boolean worseSick = this.checkWorseSick(Config._dirtyEatingWorseSickChance * filth);
            boolean sick = this.checkSick(Config._dirtyEatingSickChance * filth);
            if (worseSick || sick) {
                int change = Config._rankChangeSick + (complied ? Config._rankChangeSickForced : (byte)0);
                for (Enum.Food f : list) {
                    this._foodRanks.decRankAndCheckFavDislikeChange(f, change);
                }
                if (complied) {
                    this.setObedience(this._obedience + Config._obedienceChangeSickForced);
                }
            }
        }
    }

    public byte poop(boolean toilet) {
        if (this._alive && this._bmGauge >= this._bmMax) {
            int filth;
            this.setMood(this._mood + Config._poopMoodInc);
            int minusWeight = (int)Math.floor((double)this._baseWeight * Config._poopWeightDecCoefficient);
            minusWeight = minusWeight > Config._poopWeightLimit ? Config._poopWeightLimit : minusWeight;
            this.setWeight(this._weight - minusWeight);
            this.setBMGauge(this._bmGauge - this._bmMax);
            int n = this._baseWeight >= Config._poopIncWeightFactor ? 3 : (filth = this._baseWeight <= Config._poopIncWeightFactorSmall ? 1 : 2);
            if (this._bmGauge >= this._bmMax / 2) {
                ++filth;
                this.setWeight(this._weight - (int)Math.ceil(minusWeight / 2));
                this._bmGauge = 0;
            }
            if (!toilet) {
                this.addFilth(filth);
                this.setObedience(this._obedience + Config._floorPoopObedienceChange);
            }
            return (byte)filth;
        }
        return 0;
    }

    private void startPoop() {
        if (Utility.containsState(Utility.ENABLE_DURING_STATE, this._currentState) && (!this._asleep || this._bmGauge >= this._bmMax * 2) && this._bmGauge >= this._bmMax) {
            this.doPoop();
        } else if (!this._asleep && this._bmGauge >= this._bmMax) {
            this.setMood(this._mood + Config._postponePoopMoodChange);
        }
    }

    private void doPoop() {
        if (this.poopable()) {
            if (this.isToiletTrained()) {
                if (this._items.get(82).getCurrentUses() > 0) {
                    this.addToQueue(Enum.State.SelfToilet);
                } else if (this._items.get(83).getCurrentUses() > 0) {
                    this.addToQueue(Enum.State.SelfPortToilet);
                } else {
                    this.addToQueue(Enum.State.Pooping);
                }
            } else {
                this.addToQueue(Enum.State.Pooping);
            }
        } else if (this.isToiletTrained()) {
            if (!this._isHome) {
                if (this._world.getCurrentZone().isTown() != null && this._items.get(82).getCurrentUses() > 0) {
                    this.addToQueue(Enum.State.SelfToilet);
                } else if (this._items.get(83).getCurrentUses() > 0) {
                    this.addToQueue(Enum.State.SelfPortToilet);
                } else {
                    this.addToQueue(Enum.State.Pooping_Outside_Move);
                }
            } else if (this._isHome) {
                if (this._items.get(82).getCurrentUses() > 0) {
                    this.addToQueue(Enum.State.SelfToilet);
                } else if (this._items.get(83).getCurrentUses() > 0) {
                    this.addToQueue(Enum.State.SelfPortToilet);
                } else {
                    this.addToQueue(Enum.State.Pooping_Outside_Move);
                }
            } else {
                this.addToQueue(Enum.State.Pooping_Outside_Move);
            }
        } else {
            this.addToQueue(Enum.State.Pooping_Outside_Move);
        }
    }

    public void checkWorseExerciseInj(Enum.Attribute trainingAttribute, boolean complied) {
        boolean worsenedInjury = false;
        byte geriatricMod = 0;
        int energyMod = (int)(-((double)this._energy * (this._energy < 0 ? Config._worseInjuryNegativeEnergyCoefficient : 0.0)));
        if (this.isInj()) {
            Random random = new Random();
            int r = random.nextInt(Config._worseInjuryChance);
            byte mod1 = Config._worseInjuryBadWeightNoVitamin;
            byte mod2 = Config._worseInjuryGoodWeightNoVitamin;
            byte mod3 = Config._worseInjuryGoodWeightVitamin;
            byte mod4 = Config._worseInjuryBadWeightVitamin;
            if (this._attributeRanks.getAversion() == trainingAttribute) {
                mod1 = Config._worseWeakInjuryBadWeightNoVitamin;
                mod2 = Config._worseWeakInjuryGoodWeightNoVitamin;
                mod3 = Config._worseWeakInjuryGoodWeightVitamin;
                mod4 = Config._worseWeakInjuryBadWeightVitamin;
            }
            if (this.isGeriatric()) {
                geriatricMod = Config._worseInjuryGeriatricFactor;
            }
            int injChance = geriatricMod + (this.isFatigued() ? Config._fatigueMod : (byte)0) + energyMod + this.getCompatibilityInjChange();
            if (!(this._overweight != Enum.Weight.Under && this._overweight != Enum.Weight.Over || this.hasVitamin() || r >= mod1 + injChance)) {
                worsenedInjury = true;
            } else if (this._overweight == Enum.Weight.Healthy && !this.hasVitamin() && r < mod2 + injChance) {
                worsenedInjury = true;
            } else if (this._overweight == Enum.Weight.Healthy && this.hasVitamin() && r < mod3 + injChance) {
                worsenedInjury = true;
            } else if ((this._overweight == Enum.Weight.Under || this._overweight == Enum.Weight.Over) && this.hasVitamin() && r < mod4 + injChance) {
                worsenedInjury = true;
            }
            if (worsenedInjury) {
                this.worsenedInjury(trainingAttribute, Config._rankChangeInjury + (complied ? Config._rankChangeInjuryForced : (byte)0));
                if (trainingAttribute == Enum.Attribute.None) {
                    this._moodRank += Config._rankChangeMoodInjury + (complied ? Config._rankChangeInjuryForced : (byte)0);
                }
                if (complied) {
                    this.setObedience(this._obedience + Config._obedienceChangeInjuryForced);
                }
            }
        }
    }

    private void worsenedInjury(Enum.Attribute a, int rankChange) {
        this.setObedience(this._obedience + Config._worseMaladyObedienceDec);
        this.setMood(this._mood + Config._worseMaladyMoodDec);
        this.setEnthusiasm((byte)(this._enthusiasm + Config._worseInjuryEnthusiasmChange));
        this._timeRanks.decRankAndCheckFavDislikeChange(this.checkTime(this._clock.getHours()), Config._rankChangeInjury);
        this.setInjLength(this._injLength + 1);
        this.setEnergy((byte)(this._energy - Config._worseInjuryEnergyDec));
        this.setTotalLifespan(this._totalLifespan - (long)Config._worseInjuryLifeDec);
        if (a != Enum.Attribute.None) {
            this._attributeRanks.decRankAndCheckFavDislikeChange(a, rankChange);
        }
        if (Config._enableLifePenaltyAnim) {
            this.setStateNoRepeat(Enum.State.Bad_Health_Jeering);
        }
    }

    private void checkExerciseInj(Enum.Attribute trainingAttribute, boolean complied) {
        this.checkWorseExerciseInj(trainingAttribute, complied);
        if (!this.isInj()) {
            byte geriatricMod = 0;
            int energyMod = (int)(-((double)this._energy * (this._energy < 0 ? Config._injuryNegativeEnergyCoefficient : 0.0)));
            int fMod = this.isFatigued() ? Config._fatigueMod * Config._injuryFatigueCoefficient : 0;
            Random random = new Random();
            int r = random.nextInt(Config._injuryChance);
            int mod1 = Config._injuryBadWeightNoVitamin;
            byte mod2 = Config._injuryGoodWeightNoVitamin;
            byte mod3 = Config._injuryGoodWeightVitamin;
            byte mod4 = Config._injuryBadWeightVitamin;
            if (this._attributeRanks.getAversion() == trainingAttribute) {
                mod1 = Config._weakInjuryBadWeightNoVitamin;
                mod2 = Config._weakInjuryGoodWeightNoVitamin;
                mod3 = Config._weakInjuryGoodWeightVitamin;
                mod4 = Config._weakInjuryBadWeightVitamin;
            }
            if (this.isGeriatric()) {
                geriatricMod = Config._injuryGeriatricFactor;
            }
            int change = Config._rankChangeInjury + (complied ? Config._rankChangeInjuryForced : (byte)0);
            int injChance = geriatricMod + fMod + energyMod + this.getCompatibilityInjChange();
            if (!(this._overweight != Enum.Weight.Under && this._overweight != Enum.Weight.Over || this.hasVitamin() || r >= mod1 + injChance)) {
                this.injure(trainingAttribute, change);
            } else if (this._overweight == Enum.Weight.Healthy && !this.hasVitamin() && r < mod2 + injChance) {
                this.injure(trainingAttribute, change);
            } else if (this._overweight == Enum.Weight.Healthy && this.hasVitamin() && r < mod3 + injChance) {
                this.injure(trainingAttribute, change);
            } else if ((this._overweight == Enum.Weight.Under || this._overweight == Enum.Weight.Over) && this.hasVitamin() && r < mod4 + injChance) {
                this.injure(trainingAttribute, change);
            }
            if (this.isInj()) {
                if (trainingAttribute == Enum.Attribute.None) {
                    this._moodRank += Config._rankChangeMoodInjury + (complied ? Config._rankChangeInjuryForced : (byte)0);
                }
                if (complied) {
                    this.setObedience(this._obedience + Config._obedienceChangeInjuryForced);
                }
            }
        }
    }

    private int getCompatibilityInjChange() {
        Habitat h = this.getCurrentHabitat();
        return (this.compatibleElement(this._element, h) ? Config._compatibleElementInjChanceChange : (byte)0) + (this.compatibleField(this._field, h) ? Config._compatibleFieldInjChanceChange : (byte)0) + (this.incompatibleField(this._field, h) ? Config._incompatibleFieldInjChanceChange : (byte)0) + (this.incompatibleElement(this._element, h) ? Config._incompatibleElementInjChanceChange : (byte)0);
    }

    public void checkBattleInj(Enum.Attribute a, boolean won, boolean complied) {
        byte winMod = 0;
        byte geriatricMod = 0;
        int fMod = this.isFatigued() ? Config._fatigueMod * Config._battleInjuryFatigueCoefficient : 0;
        int energyMod = (int)(-((double)this._energy * (this._energy < 0 ? Config._battleInjuryNegativeEnergyCoefficient : 0.0)));
        if (!won) {
            winMod = Config._battleInjuryWonFactor;
        }
        if (this.isGeriatric() || this._growthStage == Enum.Stage.Fresh || this._growthStage == Enum.Stage.InTraining) {
            geriatricMod = Config._battleInjuryBadAgeFactor;
        }
        this.checkWorseBattleInj(a, won, complied);
        int injChance = fMod + geriatricMod + winMod + energyMod + this.getCompatibilityInjChange();
        if (!this.isInj()) {
            Random random = new Random();
            int r = random.nextInt(Config._battleInjuryChance);
            if (!(this._overweight != Enum.Weight.Under && this._overweight != Enum.Weight.Over || this.hasVitamin() || r >= Config._battleInjuryBadWeightNoVitamin + injChance)) {
                this.injure(a, won ? Config._rankChangeInjuryBattleWon : Config._rankChangeInjuryBattleLost);
            } else if (this._overweight == Enum.Weight.Healthy && !this.hasVitamin() && r < Config._battleInjuryGoodWeightNoVitamin + injChance) {
                this.injure(a, won ? Config._rankChangeInjuryBattleWon : Config._rankChangeInjuryBattleLost);
            } else if (this._overweight == Enum.Weight.Healthy && this.hasVitamin() && r < Config._battleInjuryGoodWeightVitamin + injChance) {
                this.injure(a, won ? Config._rankChangeInjuryBattleWon : Config._rankChangeInjuryBattleLost);
            } else if ((this._overweight == Enum.Weight.Under || this._overweight == Enum.Weight.Over) && this.hasVitamin() && r < Config._battleInjuryBadWeightVitamin + injChance) {
                this.injure(a, won ? Config._rankChangeInjuryBattleWon : Config._rankChangeInjuryBattleLost);
            }
            if (this.isInj()) {
                if (complied) {
                    this.setObedience(this._obedience + (won ? Config._obedienceChangeInjuryBattleWonForced : Config._obedienceChangeInjuryBattleLostForced));
                }
                this._moodRank += won ? Config._rankChangeMoodInjuryBattleWon : Config._rankChangeMoodInjuryBattleLost;
                this.changeBattleRanks(a, (won ? Config._rankChangeInjuryBattleWon : Config._rankChangeInjuryBattleLost) + (complied ? Config._rankChangeInjuryForced : (byte)0));
            }
        }
    }

    public void changeBattleRanks(Enum.Attribute oppAttribute, int change) {
        if (oppAttribute != Enum.Attribute.None) {
            this._attributeRanks.decRankAndCheckFavDislikeChange(oppAttribute, change);
        } else {
            this._attributeRanks.decRankAndCheckFavDislikeChange(Enum.Attribute.Vaccine, change);
            this._attributeRanks.decRankAndCheckFavDislikeChange(Enum.Attribute.Data, change);
            this._attributeRanks.decRankAndCheckFavDislikeChange(Enum.Attribute.Virus, change);
        }
    }

    public void changeTrainingRank(Enum.Attribute attribute, int change) {
        switch (attribute) {
            case None: {
                this.changeMoodRank(change);
                break;
            }
            default: {
                this._attributeRanks.decRankAndCheckFavDislikeChange(attribute, change);
            }
        }
    }

    public void checkWorseTravelInj(Enum.Attribute a, boolean walk) {
        this.calcWorseBattleInj(a, walk);
    }

    public void checkWorseBattleInj(Enum.Attribute a, boolean won, boolean complied) {
        if (this.calcWorseBattleInj(a, won)) {
            if (complied) {
                this.setObedience(this._obedience + (won ? Config._obedienceChangeInjuryBattleWonForced : Config._obedienceChangeInjuryBattleLostForced));
            }
            this._moodRank += won ? Config._rankChangeMoodInjuryBattleWon : Config._rankChangeMoodInjuryBattleLost;
            this.changeBattleRanks(a, Config._rankChangeInjury + (complied ? Config._rankChangeInjuryForced : (byte)0));
        }
    }

    private boolean calcWorseBattleInj(Enum.Attribute a, boolean won) {
        boolean worsenedInjury = false;
        byte winMod = 0;
        byte geriatricMod = 0;
        int energyMod = (int)(-((double)this._energy * (this._energy < 0 ? Config._battleWorseInjuryNegativeEnergyCoefficient : 0.0)));
        if (this.isGeriatric() || this._growthStage == Enum.Stage.Fresh || this._growthStage == Enum.Stage.InTraining) {
            geriatricMod = Config._worseBattleInjuryBadAgeFactor;
        }
        if (!won) {
            winMod = Config._worseBattleInjuryWonFactor;
        }
        int injChance = (this.isFatigued() ? Config._fatigueMod : (byte)0) + geriatricMod + winMod + energyMod + this.getCompatibilityInjChange();
        if (this.isInj()) {
            Random random = new Random();
            int r = random.nextInt(Config._worseBattleInjuryChance);
            if (!(this._overweight != Enum.Weight.Under && this._overweight != Enum.Weight.Over || this.hasVitamin() || r >= Config._worseBattleInjuryBadWeightNoVitamin + injChance)) {
                worsenedInjury = true;
            } else if (this._overweight == Enum.Weight.Healthy && !this.hasVitamin() && r < Config._worseBattleInjuryGoodWeightNoVitamin + injChance) {
                worsenedInjury = true;
            } else if (this._overweight == Enum.Weight.Healthy && this.hasVitamin() && r < Config._worseBattleInjuryGoodWeightVitamin + injChance) {
                worsenedInjury = true;
            } else if ((this._overweight == Enum.Weight.Under || this._overweight == Enum.Weight.Over) && this.hasVitamin() && r < Config._worseBattleInjuryBadWeightVitamin + injChance) {
                worsenedInjury = true;
            }
            if (worsenedInjury) {
                this.worsenedInjury(a, won ? Config._rankChangeInjuryBattleWon : Config._rankChangeInjuryBattleLost);
            }
        }
        return worsenedInjury;
    }

    public boolean checkSick(int prob) {
        return this.checkSick(prob, Config._sickChance);
    }

    public boolean checkSick(int target, int bound) {
        if (!this.isSick()) {
            Habitat h = this.getCurrentHabitat();
            int change = (this.compatibleElement(this._element, h) ? Config._compatibleElementSickChanceChange : (byte)0) + (this.compatibleField(this._field, h) ? Config._compatibleFieldSickChanceChange : (byte)0) + (this.incompatibleField(this._field, h) ? Config._incompatibleFieldSickChanceChange : (byte)0) + (this.incompatibleElement(this._element, h) ? Config._incompatibleElementSickChanceChange : (byte)0);
            if (Utility.randomChance(target, bound + change - (this.isGeriatric() ? Config._sickGeriatricFactor : (byte)0))) {
                this.sicken();
                return true;
            }
            return false;
        }
        return false;
    }

    public boolean checkWorseSick(int target, int bound) {
        if (this.isSick()) {
            if (Utility.randomChance(target, bound)) {
                this.setSickLength(this._sickLength + 1);
                this.setTotalLifespan(this._totalLifespan - (long)Config._worseSickLifeDec);
                this.setObedience(this._obedience + Config._worseMaladyObedienceDec);
                this.setMood(this._mood + Config._worseMaladyMoodDec);
                this.setEnthusiasm((byte)(this._enthusiasm + Config._worseSickEnthusiasmChange));
                this._timeRanks.decRankAndCheckFavDislikeChange(this.checkTime(this._clock.getHours()), Config._rankChangeSick);
                if (Config._enableLifePenaltyAnim) {
                    this.setStateNoRepeat(Enum.State.Bad_Health_Jeering);
                }
                this.startPoop();
                return true;
            }
            return false;
        }
        return false;
    }

    public boolean checkWorseSick(int prob) {
        return this.checkWorseSick(prob + (this.isFatigued() ? Config._fatigueMod : (byte)0), Config._worseSickChance - (this.isGeriatric() ? Config._worseSickGeriatricFactor : (byte)0));
    }

    public boolean isGeriatric() {
        boolean isGeriatric = false;
        if (this._lapsedLife >= 0L) {
            long lifeRemainder = this._totalLifespan - this._lapsedLife;
            if (!(lifeRemainder > (long)Config._geriatricAge && (this._minToDecayHunger + this._minToDecayStrength) / 2 > Config._needDecayMinAsGeriatric || this._growthStage.equals((Object)Enum.Stage.Fresh) || this._growthStage.equals((Object)Enum.Stage.InTraining) || this._growthStage.equals((Object)Enum.Stage.Egg))) {
                isGeriatric = true;
            } else if (this._totalLifespan <= this._growthPeriod && (this._growthStage.equals((Object)Enum.Stage.Fresh) || this._growthStage.equals((Object)Enum.Stage.InTraining)) && !this._growthStage.equals((Object)Enum.Stage.Egg)) {
                isGeriatric = true;
            }
        } else {
            isGeriatric = true;
        }
        return isGeriatric;
    }

    private void fatigue(Enum.Attribute a, int moodRankChange, boolean complied) {
        this.fatigue(complied);
        int change = Config._rankChangeFatigue + (complied ? Config._rankChangeFatigueForced : (byte)0);
        if (complied) {
            this.setObedience(this._obedience + Config._obedienceChangeFatigueForced);
        }
        if (a != null) {
            if (a == Enum.Attribute.None) {
                this._attributeRanks.decRankAndCheckFavDislikeChange(Enum.Attribute.Vaccine, change);
                this._attributeRanks.decRankAndCheckFavDislikeChange(Enum.Attribute.Data, change);
                this._attributeRanks.decRankAndCheckFavDislikeChange(Enum.Attribute.Virus, change);
            } else {
                this._attributeRanks.decRankAndCheckFavDislikeChange(a, change);
            }
        }
        this.changeMoodRank(moodRankChange);
    }

    private void fatigue(boolean complied) {
        if (Config._canFatigue) {
            Habitat h;
            this._timeRanks.decRankAndCheckFavDislikeChange(this.checkTime(this._clock.getHours()), Config._rankChangeFatigue);
            if (this.checkWorseSick(Config._fatigueWorseSickChance) && complied) {
                this.setObedience(this._obedience + Config._obedienceChangeSickForced);
            }
            int change = (this.compatibleElement(this._element, h = this.getCurrentHabitat()) ? Config._compatibleElementFatigueLengthChange : (byte)0) + (this.compatibleField(this._field, h) ? Config._compatibleFieldFatigueLengthChange : (byte)0) + (this.incompatibleField(this._field, h) ? Config._incompatibleFieldFatigueLengthChange : (byte)0) + (this.incompatibleElement(this._element, h) ? Config._incompatibleElementFatigueLengthChange : (byte)0);
            if (this.isFatigued()) {
                this.setFatigueLength(this._fatigueLength + (byte)Utility.randomBetween(Config._fatigueMin, Config._fatigueMax + change));
                this._mistakeDay += Config._fatigueMissedDay;
                this.checkSick(Config._alreadyFatiguedSickChance);
                this.setEnthusiasm((byte)(this._enthusiasm + Config._alreadyFatiguedEnthusiasmChange));
                this.setMood(this._mood - Config._alreadyFatiguedMoodDec);
                this.setObedience(this._obedience - Config._alreadyFatiguedObedienceDec);
                if (this.isGeriatric()) {
                    this.setTotalLifespan(this._totalLifespan - (long)Config._geriatricFatigueLifeDec);
                    this._energy = (byte)(this._energy - Config._geriatricFatigueEnergyDec);
                }
            } else {
                this.setFatigueLength((byte)Utility.randomBetween(Config._fatigueMin, Config._fatigueMax + change));
                if (Config._fatigueCareMistake) {
                    this.incMistake();
                } else {
                    this._mistakeDay += Config._fatigueMissedDay;
                }
            }
            if (Config._enableLifePenaltyAnim) {
                this.setStateNoRepeat(Enum.State.Bad_Health_Jeering);
            }
            this._energy = (byte)(this._energy - Config._fatigueEnergyDec);
            this.setTotalLifespan(this._totalLifespan - (long)Config._fatigueLifeDec);
            this.setEnthusiasm((byte)(this._enthusiasm + Config._fatigueEnthusiasmChange));
            this.setMood(this._mood - Config._fatigueMoodDec);
        }
    }

    public void disturb(int moodRankChange) {
        if (this.disturb()) {
            this.changeMoodRank(moodRankChange);
        }
    }

    public void disturb(Enum.Attribute a) {
        if (this.disturb()) {
            if (a == Enum.Attribute.None) {
                this._attributeRanks.decRankAndCheckFavDislikeChange(Enum.Attribute.Vaccine, Config._rankChangeDisturb);
                this._attributeRanks.decRankAndCheckFavDislikeChange(Enum.Attribute.Data, Config._rankChangeDisturb);
                this._attributeRanks.decRankAndCheckFavDislikeChange(Enum.Attribute.Virus, Config._rankChangeDisturb);
            } else {
                this._attributeRanks.decRankAndCheckFavDislikeChange(a, Config._rankChangeDisturb);
            }
        }
    }

    public void disturb(FoodType food) {
        if (this.disturb()) {
            for (Enum.Food f : food.getType()) {
                this._foodRanks.decRankAndCheckFavDislikeChange(f, Config._rankChangeDisturb);
            }
        }
    }

    public boolean disturb() {
        boolean d = false;
        if (this._asleep) {
            if (!this._nap) {
                d = true;
                if (this._restless < 0) {
                    this.setStateNoRepeat(Enum.State.Jeering);
                } else {
                    this.setStateNoRepeat(Enum.State.Sad_Jeering);
                }
                if (this._awakeLapse >= Config._maxMinutesToFullAwakeDisturb - this._restless * Config._maxMinutesToFullAwakeDisturbRestlessCoefficient || this._energy >= this._maxEnergy) {
                    this.setAwakeLapse(this._awakeLimit);
                    this._sleepLapse = 0;
                } else {
                    int postpone = Utility.randomBetween(Config._disturbPostponeMin, Config._disturbPostponeMax);
                    this.setSleepLapse(this._sleepLimit - postpone);
                    this.setAwakeLapse(this._awakeLapse - postpone);
                }
                this._mistakeDay += Config._disturbMistakeDayChange;
                this.setDisturb((byte)(this._disturb + 1));
                this._timeRanks.decRankAndCheckFavDislikeChange(this.checkTime(this._clock.getHours()), Config._rankChangeDisturb);
                this.checkWorseSick(Config._disturbWorseSickChance);
                if (this._disturb >= Config._disturbLimitCheckSick) {
                    this.checkSick(Config._disturbSickChance);
                }
            }
            this.setMood(this._mood - (this._restless == 0 ? Config._disturbMoodDec : (this._restless == 1 ? Config._disturbMoodDecRestless : Config._disturbMoodDecNotRestless)));
            this.setEnthusiasm((byte)(this._enthusiasm - (this._restless == 0 ? Config._disturbEnthusiasmDec : (this._restless == 1 ? Config._disturbEnthusiasmDecRestless : Config._disturbEnthusiasmDecNotRestless))));
            this.setAsleep(false);
            this.setLights(true);
        }
        return d;
    }

    public void vitaminLapse(byte currentMin) {
        if (currentMin % Config._vitaminLapseMin == 0 && this.hasVitamin()) {
            this.setVitaminLapse((byte)(this._vitaminLapse - 1));
        }
    }

    public void bandageLapse(byte currentMin) {
        if (currentMin % Config._bandageLapseMin == 0 && this.getBandage()) {
            this.setBandageLapse((byte)(this._bandageLapse - 1));
        }
    }

    public boolean sleepNotNap() {
        return this._sleepLapse >= this._sleepLimit - (Config._sleepNotNapMinutes - this._restless * Config._sleepNotNapMinutesRestlessCoefficient);
    }

    private void checkNap() {
        if (!(this._asleep || this._lights || this._nap)) {
            this._napEnergyInc = 0;
            this._napCycle = 0;
            if (this.sleepNotNap()) {
                this.sleep();
            } else {
                this.setNap(true);
                this.setMood(this._mood + Config._onNapMoodInc);
                if (!this.isSick() && !this.isInj()) {
                    if (this._awakeLimit - this._sleepLapse == this._awakeLimit - Config._minutesHour && Config._minutesHour - this._clock.getMinutes() <= Config._minutesHour / 6) {
                        this.setAwakeLapse(this._awakeLimit - 2 * Config._minutesHour);
                    } else {
                        this.setAwakeLapse(this._awakeLimit - this._sleepLapse);
                    }
                } else if (Config._minutesHour - this._clock.getMinutes() <= Config._minutesHour / 6) {
                    this.setAwakeLapse(this._awakeLimit - 2 * Config._minutesHour);
                } else {
                    this.setAwakeLapse(this._awakeLimit - Config._minutesHour);
                }
            }
        }
    }

    public void medLapse(byte currentMin) {
        if (currentMin % Config._medLapseMin == 0 && this.getMed()) {
            this.setMedLapse((byte)(this._medLapse - 1));
        }
    }

    public void sickLapse(byte currentMin) {
        if (currentMin % Config._sickLapseMin == 0 && this.isSick()) {
            this.sickPenalty();
            this.setSickLength(this._sickLength - 1);
        }
    }

    private void sickPenalty() {
        if (!this._asleep) {
            this.changeNutrition(Config._sickNutritionChange);
            this.setBMGauge(this._bmGauge + this._bmLapseInc + Config._sickLapsePenaltyBM);
            this.startPoop();
        }
    }

    public void injuryLapse(byte currentMin) {
        if (currentMin % Config._injLapseMin == 0 && this.isInj()) {
            this.injuryPenalty();
            this.setInjLength(this._injLength - 1);
        }
    }

    private void injuryPenalty() {
        if (!this._asleep) {
            this.changeNutrition(Config._injuryNutritionChange);
            this.setHunger((byte)(this._hunger - Config._injuryLapsePenaltyHunger));
        }
    }

    private void overeatPenalty(FoodType food, boolean complied) {
        this.setCurrentState(Enum.State.Jeering);
        ++this._overeat;
        this._timeRanks.decRankAndCheckFavDislikeChange(this.checkTime(this._clock.getHours()), Config._rankChangeOvereat);
        if (food != null && food.getType() != null) {
            for (Enum.Food f : food.getType()) {
                int change = Config._rankChangeOvereat + (complied ? Config._rankChangeOvereatForced : (byte)0);
                this._foodRanks.decRankAndCheckFavDislikeChange(f, change);
            }
        }
        this.setMood(this._mood - (this._glutton == 0 ? Config._overeatMoodPenalty : (this._glutton == 1 ? Config._overeatMoodPenaltyGlutton : Config._overeatMoodPenaltyNotGlutton)));
        this.setObedience(this._obedience - (this._glutton == 0 ? Config._overeatObediencePenalty : (this._glutton == 1 ? Config._overeatObediencePenaltyGlutton : Config._overeatObediencePenaltyNotGlutton)));
    }

    private void stomachCapacityPenalty(int newHunger, FoodType food, boolean complied) {
        this._bmGauge = this._bmMax + (newHunger - Config._fullHunger);
        this._hunger = Config._fullHunger;
        if (this._calories > Config._caloriesStomachCapacityPenalty) {
            this._calories = Config._caloriesStomachCapacityPenalty;
        }
        if (food != null && food.getType() != null) {
            for (Enum.Food f : food.getType()) {
                int change = Config._rankChangeStomachLimit + (complied ? Config._rankChangeStomachLimitForced : (byte)0);
                this._foodRanks.decRankAndCheckFavDislikeChange(f, change);
            }
            if (complied) {
                this.setObedience(this._obedience + Config._obedienceChangeStomachLimitForced);
            }
        }
        this.setMood(this._mood - (this._glutton == 0 ? Config._stomachMaxMoodPenalty : (this._glutton == 1 ? Config._stomachMaxMoodPenaltyGlutton : Config._stomachMaxMoodPenaltyNotGlutton)));
        this._timeRanks.decRankAndCheckFavDislikeChange(this.checkTime(this._clock.getHours()), Config._rankChangeStomachLimit);
        this.setEnthusiasm((byte)(this._enthusiasm - (this._glutton == 0 ? Config._stomachMaxEnthusiasmPenalty : (this._glutton == 1 ? Config._stomachMaxEnthusiasmPenaltyGlutton : Config._stomachMaxEnthusiasmPenaltyNotGlutton))));
        this.setObedience(this._obedience - (this._glutton == 0 ? Config._stomachMaxObediencePenalty : (this._glutton == 1 ? Config._stomachMaxObediencePenaltyGlutton : Config._stomachMaxObediencePenaltyNotGlutton)));
        this._mistakeDay += Config._overStomachCapcityMistakeDayChange;
        this.changeNutrition(Config._overeatNutritionChange);
        this.doPoop();
    }

    private void toNapSleepLapse(byte currentMin) {
        if (this._growthStage != Enum.Stage.Egg && currentMin % Config._toNapSleepMin == 0) {
            if (!this._lights && !this._asleep) {
                this._toNapSleepLapse = (byte)(this._toNapSleepLapse + 1);
                if (this._toNapSleepLapse >= this.calcToSleepNapLapse()) {
                    this.checkNap();
                    this._toNapSleepLapse = 0;
                }
            } else {
                this._toNapSleepLapse = 0;
            }
        }
    }

    private byte calcToSleepNapLapse() {
        byte untilNap = 0;
        int obedienceMod = 1;
        int r = this._restless * Config._toSleepNapLapseRestlessCoefficient;
        if (this._obedience >= Config._toNapObedienceFactor) {
            obedienceMod = 0;
        }
        untilNap = this._energy > this._maxEnergy / 2 ? (byte)(Config._toNapHighEnergyFactor + r + obedienceMod) : (byte)(Config._toNapLowEnergyFactor + r + obedienceMod);
        return untilNap;
    }

    private void sleepDecay(byte currentMin) {
        if (this._growthStage != Enum.Stage.Egg && currentMin % Config._sleepDecayMin == 0 && this._alive) {
            if (!this._asleep) {
                this.setSleepLapse(this._sleepLapse + this._sleepLapseInc);
            } else {
                int i = this._awakeLapseInc;
                if (this._lights && !this.pauseCall() && Utility.randomChance(Config._lightsOnAwakeLapseUnchangedChance, 100)) {
                    i = 0;
                } else {
                    this.setAwakeLapse(this._awakeLapse + i);
                }
                if (this._nap) {
                    ++this._napCycle;
                    this.setSleepLapse(this._sleepLapse - i);
                    if (this._napCycle >= Config._changeNapToSleepMinutes + this._restless * Config._changeNapToSleepMinutesRestlessCoefficient) {
                        this._sleepMinutes += this._napEnergyInc - 1;
                        this.incSleepMinutes(this._energy < 0 ? Config._negativeEnergyGain : this._energyGain);
                        this._sleepLapse = 0;
                        this._nap = false;
                    }
                } else {
                    this.incSleepMinutes(this._energy < 0 ? Config._negativeEnergyGain : this._energyGain);
                }
            }
        }
    }

    public int getNapToSleepPercent() {
        return (int)(100.0 * ((double)this._napCycle / ((double)Config._changeNapToSleepMinutes + (double)(this._restless * Config._changeNapToSleepMinutesRestlessCoefficient))));
    }

    private void hungerDecay() {
        if (this._alive && (!this._asleep || this._hunger > Config._sleepMinHungerDecay)) {
            byte hungerDec = 1;
            this.setHunger((byte)(this._hunger - hungerDec));
        }
    }

    private void poopWaitMoodCheck(byte currentMin) {
        if (this._growthStage != Enum.Stage.Egg && this._bmGauge >= this._bmMax && currentMin % Config._poopWaitMin == 0) {
            if ((double)this._bmGauge >= (double)this._bmMax * 1.5) {
                this.setMood(this._mood + Config._largePoopWaitMoodChange);
            } else {
                this.setMood(this._mood + Config._poopWaitMoodChange);
            }
        }
    }

    private void bmLapse(byte currentMin) {
        if (this._growthStage != Enum.Stage.Egg && currentMin % Config._bmLapseMin == 0) {
            this.startPoop();
        }
    }

    private void exerciseDecay() {
        if (!(!this._alive || this._energy <= 0 && this._exercise <= Config._strengthMinZeroEnergy || this._asleep && this._exercise <= Config._sleepMinStrengthDecay)) {
            byte exerciseDec = 1;
            this.setExercise((byte)(this._exercise - exerciseDec));
        }
    }

    private void prioritizeStateInQueue(Enum.State s) {
        if (this.canQueue(s)) {
            if (!this._animQueue.isEmpty()) {
                this._animQueue.add(0, s);
            } else {
                this._animQueue.add(s);
            }
        }
    }

    private void addToQueue(Enum.State currentState) {
        if (this.canQueue(currentState)) {
            this._animQueue.add(currentState);
        }
    }

    private boolean canQueue(Enum.State s) {
        return s != Enum.State.Idling && !this._animQueue.contains((Object)s);
    }

    public String getModFolder() {
        return this._tournamentVersion ? "\\/:*?\"<>|" : this.MOD_FOLDER + "csv/";
    }

    public String getModelFolder() {
        return this.MODEL_FOLDER;
    }

    public int getMajority(int[] array) {
        int i;
        int max = 0;
        int index = -1;
        for (i = 0; i < array.length; ++i) {
            if (array[i] <= max) continue;
            max = array[i];
            index = i;
        }
        for (i = 0; i < array.length; ++i) {
            if (max != array[i] || index == i) continue;
            index = -1;
            break;
        }
        return index;
    }

    public void createWorld() {
        this._world = new WorldMap(this, this.getModFolder(), this.MODEL_FOLDER);
    }

    public boolean canEscape(Enemy enemy) {
        boolean escaped = false;
        Random r = new Random();
        int power = this._vaccinePower + this._dataPower + this._virusPower + this._fullHealthPoints;
        int enemyPower = enemy.getOppGreen() + enemy.getOppRed() + enemy.getOppYellow() + enemy.getEnemyHealth() + (enemy.getIsZoneBoss() ? Config._bossEscapeChance : (enemy.getIsRandom() ? Config._randomEscapeChance : (byte)0));
        int prob = r.nextInt(power + enemyPower);
        if (prob <= power) {
            escaped = true;
        }
        return escaped;
    }

    public void seasonChange(Enum.Season old) {
        ArrayList<Trophy> trophies = null;
        switch (old) {
            case Spring: {
                trophies = this._tournament.getSpringTrophies();
                break;
            }
            case Summer: {
                trophies = this._tournament.getSummerTrophies();
                break;
            }
            case Fall: {
                trophies = this._tournament.getFallTrophies();
                break;
            }
            case Winter: {
                trophies = this._tournament.getWinterTrophies();
            }
        }
        if (trophies != null) {
            for (Trophy t : trophies) {
                if (!t.getResetWon()) continue;
                t.setSeasonBeat(false);
            }
        }
    }

    public void dailyChange() {
        this._foughtTrophiesToday.clear();
        this._dailyTrophies.clear();
        this.setTrophySchedule();
        this.setDayTemp();
        this._tourneyAlarm = -1;
        this._homeFoodShop.clear();
        this._homeItemShop.clear();
        for (MapLevel m : this._world.getMaps()) {
            if (m == null) continue;
            for (Zone z : m.getZones()) {
                if (z == null) continue;
                for (Town t : z.getTowns()) {
                    if (t == null) continue;
                    t.resetDailyShops();
                }
            }
        }
        this.autoSave();
    }

    public void restockItemShop() {
        if (!this._isHome) {
            ArrayList<ShopConsumable> shop;
            Town t = this._world.getCurrentZone().isTown();
            if (t != null && this.canRestock(shop = t.getItemShop())) {
                t.restockItemShop(this);
            }
        } else if (this.canRestock(this._homeItemShop)) {
            ArrayList<Consumable> iList = new ArrayList<Consumable>();
            iList.addAll(this._items);
            this._homeItemShop = this.restockShop(null, this._homeItemShop, iList, Config._maxItemShopInventory, false, true);
        }
    }

    public void restockFoodShop() {
        if (!this._isHome) {
            ArrayList<ShopConsumable> shop;
            Town t = this._world.getCurrentZone().isTown();
            if (t != null && this.canRestock(shop = t.getFoodShop())) {
                t.restockFoodShop(this);
            }
        } else if (this.canRestock(this._homeFoodShop)) {
            ArrayList<Consumable> iList = new ArrayList<Consumable>();
            iList.addAll(this._foodTypes);
            this._homeFoodShop = this.restockShop(null, this._homeFoodShop, iList, Config._maxFoodShopInventory, true, true);
        }
    }

    private boolean canRestock(ArrayList<ShopConsumable> shop) {
        boolean r = false;
        if (this._restock > 0 && shop != null && !shop.isEmpty()) {
            for (ShopConsumable c : shop) {
                if (c.getCurrentStock() != 0) continue;
                r = true;
                break;
            }
        }
        return r;
    }

    private ArrayList<ShopConsumable> restockShop(ArrayList<ShopConsumable> override, ArrayList<ShopConsumable> shop, ArrayList<Consumable> list, byte max, boolean isFood, boolean isHome) {
        ArrayList<ShopConsumable> stock = this.randomizeShop(override, list, max, isFood, isHome, false);
        ArrayList<ShopConsumable> add = new ArrayList<ShopConsumable>();
        ArrayList<ShopConsumable> remove = new ArrayList<ShopConsumable>();
        for (ShopConsumable s : shop) {
            if (s.getCurrentStock() != 0) continue;
            if (Utility.randomChance(Config._restockNewItemChance, 100)) {
                ShopConsumable validConsumable = null;
                if (!stock.isEmpty()) {
                    for (ShopConsumable c : stock) {
                        if (s.getConsumableID() == c.getConsumableID()) continue;
                        validConsumable = c;
                        break;
                    }
                }
                if (validConsumable != null) {
                    for (ShopConsumable c : shop) {
                        if (validConsumable.getConsumableID() != c.getConsumableID()) continue;
                        validConsumable = null;
                        break;
                    }
                }
                stock.remove(validConsumable);
                if (validConsumable != null) {
                    add.add(validConsumable);
                    remove.add(s);
                    continue;
                }
                s.randomizeStock();
                continue;
            }
            s.randomizeStock();
        }
        for (ShopConsumable c : remove) {
            shop.remove(c);
        }
        for (ShopConsumable c : add) {
            shop.add(c);
        }
        if (this._restock > 0) {
            this._restock = (byte)(this._restock - 1);
        }
        return shop;
    }

    private ArrayList<ShopConsumable> randomizeShop(ArrayList<ShopConsumable> override, ArrayList<Consumable> list, byte max, boolean isFood, boolean isHome, boolean checkSale) {
        ArrayList<ShopConsumable> consumables = new ArrayList<ShopConsumable>();
        Random ran = new Random();
        ArrayList<ShopConsumable> availableConsumables = new ArrayList<ShopConsumable>();
        ArrayList<ShopConsumable> mustStock = new ArrayList<ShopConsumable>();
        for (Consumable f : list) {
            if (!f.getShopUnlocked()) continue;
            ShopConsumable c = f.getHomeShop();
            if (override != null) {
                for (ShopConsumable s : override) {
                    if (f.getID() != s.getConsumableID()) continue;
                    c = s;
                    break;
                }
            }
            if (c == null || c.getPurchasePrice() <= 0 || !c.withinTime(this._clock.getHours(), this.getSeason())) continue;
            if (c.mustStock()) {
                mustStock.add(c);
                continue;
            }
            if (!Utility.randomChance(c.getStockChance()[this.getSeason().ordinal()], 100)) continue;
            availableConsumables.add(c);
        }
        this.addConsumables(ran, max, isHome, isFood, mustStock, consumables, checkSale);
        this.addConsumables(ran, max, isHome, isFood, availableConsumables, consumables, checkSale);
        return consumables;
    }

    private void addConsumables(Random ran, int max, boolean isHome, boolean isFood, ArrayList<ShopConsumable> pool, ArrayList<ShopConsumable> consumables, boolean checkSale) {
        while (consumables.size() < max && !pool.isEmpty()) {
            int prob = ran.nextInt(pool.size());
            ShopConsumable f = pool.get(prob);
            ShopConsumable c = isHome ? f : new ShopConsumable(f.getID(), f.getConsumableID(), isFood, f.getStockChance(), f.getMaxStock(), f.getMinStock(), f.getTimeAvailable(), f.getPrice(), f.mustStock(), f.getSaleChance(), f.getSaleFactor(), f.getResellFactor());
            boolean add = true;
            for (ShopConsumable s : consumables) {
                if (s.isFood() != c.isFood() || s.getConsumableID() != c.getConsumableID()) continue;
                add = false;
                break;
            }
            if (add) {
                c.randomizeStock();
                if (checkSale) {
                    c.checkSale(this.getSeason());
                }
                consumables.add(c);
            }
            pool.remove(f);
        }
    }

    public ArrayList<ShopConsumable> randomizeItemShop(ArrayList<ShopConsumable> itemOverride, byte maxItems, boolean isHome) {
        ArrayList<Consumable> iList = new ArrayList<Consumable>();
        iList.addAll(this._items);
        ArrayList<ShopConsumable> items = this.randomizeShop(itemOverride, iList, maxItems, false, isHome, true);
        return items;
    }

    public ArrayList<ShopConsumable> randomizeFoodShop(ArrayList<ShopConsumable> foodOverride, byte maxFood, boolean isHome) {
        ArrayList<Consumable> fList = new ArrayList<Consumable>();
        fList.addAll(this._foodTypes);
        ArrayList<ShopConsumable> foods = this.randomizeShop(foodOverride, fList, maxFood, true, isHome, true);
        return foods;
    }

    public ArrayList<ShopConsumable> restockItemShop(ArrayList<ShopConsumable> itemOverride, ArrayList<ShopConsumable> shop, byte maxItems, boolean isHome) {
        ArrayList<Consumable> iList = new ArrayList<Consumable>();
        iList.addAll(this._items);
        return this.restockShop(itemOverride, shop, iList, maxItems, false, isHome);
    }

    public ArrayList<ShopConsumable> restockFoodShop(ArrayList<ShopConsumable> override, ArrayList<ShopConsumable> shop, byte max, boolean isHome) {
        ArrayList<Consumable> iList = new ArrayList<Consumable>();
        iList.addAll(this._foodTypes);
        return this.restockShop(override, shop, iList, max, true, isHome);
    }

    private ArrayList<ArrayList<ShopConsumable>> randomizeShops(ArrayList<ShopConsumable> foodOverride, ArrayList<ShopConsumable> itemOverride, byte maxFood, byte maxItems, boolean isHome) {
        ArrayList<ShopConsumable> foods = this.randomizeFoodShop(foodOverride, maxFood, isHome);
        ArrayList<ShopConsumable> items = this.randomizeItemShop(itemOverride, maxItems, isHome);
        return new ArrayList<ArrayList<ShopConsumable>>(Arrays.asList(foods, items));
    }

    private int[] checkGift() {
        int[] c = null;
        Random r = new Random();
        int chance = Config._obedienceRefusalCap - this._obedience + (int)((double)(Config._maxMood - this._mood) * Config._giftChanceMoodCoefficient) + Config._giftChanceFactor;
        int giftChance = r.nextInt(chance);
        if (giftChance == 0) {
            c = this.getGift(r);
        }
        return c;
    }

    private int[] getGift(Random r) {
        int[] c = null;
        ArrayList<FoodType> giftFoods = new ArrayList<FoodType>();
        ArrayList<Item> giftItems = new ArrayList<Item>();
        for (FoodType f : this._foodTypes) {
            if (!f.canIncQuantity() || !f.getCanGift()) continue;
            giftFoods.add(f);
        }
        for (Item i : this._items) {
            if (!i.canIncQuantity() || !i.getCanGift()) continue;
            giftItems.add(i);
        }
        int totalItems = giftFoods.size() + giftItems.size();
        if (totalItems > 0) {
            int giftNum = r.nextInt(totalItems);
            c = giftNum >= giftFoods.size() ? new int[]{((Item)giftItems.get(giftNum -= giftFoods.size())).getID(), 0} : new int[]{((FoodType)giftFoods.get(giftNum)).getID(), 1};
        }
        return c;
    }

    private void checkRequest() {
    }

    private void getRequest() {
    }

    public void processRequest() {
    }

    public void save(boolean quit) {
        this.save(false, quit);
    }

    private File backup(String savePath, String finalPath) {
        String backupPath = savePath + "Backups" + File.separator + "backup_" + this._saveString;
        String oldBackup = savePath + "Backups" + File.separator + "backupOLD_" + this._saveString;
        File backup = new File(backupPath);
        File current = new File(finalPath);
        File old = new File(oldBackup);
        if (!backup.getParentFile().exists()) {
            backup.getParentFile().mkdirs();
        }
        backup.renameTo(old);
        current.renameTo(backup);
        old.delete();
        return backup;
    }

    private synchronized void save(boolean autoSave, boolean quit) {
        File backup;
        boolean doBackup;
        this._saving = true;
        String savePath = "files/saves/";
        String finalPath = savePath + this._saveString;
        boolean bl = doBackup = !autoSave && Config._backupSave && (!quit || quit && Config._backupOnSaveExit);
        if (doBackup) {
            this.backup(savePath, finalPath);
        }
        File newSave = new File(finalPath);
        String delin = ",";
        try (PrintWriter save = new PrintWriter(newSave);){
            this.writeInfo(save, new StringBuilder(), delin);
            this.writeMap(save, new StringBuilder(), delin);
            this.writeTrophies(save, new StringBuilder(), delin);
            this.writeDailyTrophies(save, new StringBuilder(), delin);
            this.writeTrophySchedule(save, new StringBuilder(), delin);
            this.writeFoods(save, new StringBuilder(), delin);
            this.writeTempRecord(save, new StringBuilder(), delin);
            this.writeHabitats(save, new StringBuilder(), delin);
            this.writeItems(save, new StringBuilder(), delin);
            this.writeDailyShopTrophies(save, new StringBuilder(), delin);
            this.writeDigimemory(save, new StringBuilder(), delin);
            this.writeGenerationHistory(save, new StringBuilder(), delin);
            this.writeDNA(save, new StringBuilder(), delin);
            this.writeHabitatRecord(save, new StringBuilder(), delin);
            this.writeObedienceRecord(save, new StringBuilder(), delin);
            this.writeCooldown(save, new StringBuilder(), delin);
            this.writeEvolutionHistory(save, new StringBuilder(), delin);
            this.writeTournament(save, new StringBuilder(), delin);
            this.writeTournamentRoster(save, new StringBuilder(), delin);
            this.writeTournamentChecked(save, new StringBuilder(), delin);
            this.writeTournamentDisqualified(save, new StringBuilder(), delin);
            this.writeLevelsFought(save, new StringBuilder(), delin);
            this.writeWeather(save, new StringBuilder(), delin);
            this.writeConsumableEffects(save, new StringBuilder(), delin);
            this.writeTowns(save, new StringBuilder(), delin);
            this.writeFoughtTrophiesToday(save, new StringBuilder(), delin);
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
            e.printStackTrace();
        }
        if (Config._autoSaveTree && autoSave || !autoSave) {
            this.saveTree();
        }
        this._settings.saveLastSettings();
        if (this._tournamentVersion) {
            Cryption.encrypt("hackero/", finalPath);
        }
        if (doBackup && (backup = this.backup(savePath, finalPath)) != null) {
            try {
                Files.copy(backup.toPath(), Paths.get(finalPath, new String[0]), StandardCopyOption.REPLACE_EXISTING);
            }
            catch (IOException iOException) {
                // empty catch block
            }
        }
        if (quit) {
            System.exit(0);
        } else {
            this._saving = false;
        }
    }

    private void writeInfo(PrintWriter save, StringBuilder info, String delin) {
        info.append(this._clock.getSeconds());
        info.append(delin);
        info.append(this._clock.getMinutes());
        info.append(delin);
        info.append(this._clock.getHours());
        info.append(delin);
        info.append(this._clock.getFastMod());
        info.append(delin);
        info.append(this._settings.getShell());
        info.append(delin);
        info.append(this._settings.getGameScale());
        info.append(delin);
        info.append(this._settings.isSound());
        info.append(delin);
        info.append(this._calorieMaxMod);
        info.append(delin);
        info.append(this._calorieMinMod);
        info.append(delin);
        info.append(this._itemInterestLapse);
        info.append(delin);
        info.append(this._foodRanks.getDisliked() != null ? this._foodRanks.getDisliked().ordinal() : Enum.Food.None.ordinal());
        info.append(delin);
        info.append(this._attributeRanks.getDisliked() != null ? this._attributeRanks.getDisliked().ordinal() : Enum.Attribute.None.ordinal());
        info.append(delin);
        info.append(this._timeRanks.getDisliked() != null ? this._timeRanks.getDisliked().ordinal() : Enum.Time.None.ordinal());
        info.append(delin);
        info.append(this._foodRanks.getFavorite().ordinal());
        info.append(delin);
        info.append(this._attributeRanks.getFavorite().ordinal());
        info.append(delin);
        info.append(this._praiseWindow);
        info.append(delin);
        info.append(this._praise);
        info.append(delin);
        info.append(this._scoldWindow);
        info.append(delin);
        info.append(this._scold);
        info.append(delin);
        info.append(this._refused);
        info.append(delin);
        info.append(this._mood);
        info.append(delin);
        info.append(this._currentMood.ordinal());
        info.append(delin);
        info.append(this._enthusiasm);
        info.append(delin);
        info.append(this._obedience);
        info.append(delin);
        info.append(this._glutton);
        info.append(delin);
        info.append(this._restless);
        info.append(delin);
        info.append(this._disposition);
        info.append(delin);
        info.append(this._lightsOffMistake);
        info.append(delin);
        info.append(this._timeSkip);
        info.append(delin);
        info.append(this._healthPoints);
        info.append(delin);
        info.append(this._index);
        info.append(delin);
        info.append(this._age);
        info.append(delin);
        info.append(this._bonus);
        info.append(delin);
        info.append(this._timeToAge);
        info.append(delin);
        info.append(this._callMinutesPoop);
        info.append(delin);
        info.append(this._toiletTrained);
        info.append(delin);
        info.append(this._hunger);
        info.append(delin);
        info.append(this._exercise);
        info.append(delin);
        info.append(this._energy);
        info.append(delin);
        info.append(this._weight);
        info.append(delin);
        info.append(this._restock);
        info.append(delin);
        info.append(this._fullHealthPoints);
        info.append(delin);
        info.append(this._attribute.ordinal());
        info.append(delin);
        info.append(this._vaccinePower);
        info.append(delin);
        info.append(this._dataPower);
        info.append(delin);
        info.append(this._virusPower);
        info.append(delin);
        info.append(this._battles);
        info.append(delin);
        info.append(this._wins);
        info.append(delin);
        info.append(this._totalLifespan);
        info.append(delin);
        info.append(this._lapsedLife);
        info.append(delin);
        info.append(0);
        info.append(delin);
        info.append(this._growthPeriod);
        info.append(delin);
        info.append(this._alive);
        info.append(delin);
        info.append(this._overweight.ordinal());
        info.append(delin);
        info.append(this._disturb);
        info.append(delin);
        info.append(this._overeat);
        info.append(delin);
        info.append(this._mistake);
        info.append(delin);
        info.append(this._mistakeDay);
        info.append(delin);
        String s = "";
        for (int i = 0; i < this._filth.length; ++i) {
            s = s + this._filth[i] + ":";
        }
        info.append(s);
        info.append(delin);
        info.append(this._bmGauge);
        info.append(delin);
        info.append(this._asleep);
        info.append(delin);
        info.append(this._lights);
        info.append(delin);
        info.append(this._callMinutesHunger);
        info.append(delin);
        info.append(this._callMinutesStrength);
        info.append(delin);
        info.append(this._sickCount);
        info.append(delin);
        info.append(this._injCount);
        info.append(delin);
        info.append(this._vitaminLapse);
        info.append(delin);
        info.append(this._callMinutesLights);
        info.append(delin);
        info.append(this._bandageLapse);
        info.append(delin);
        info.append(this._callMinutesDiscipline);
        info.append(delin);
        info.append(this._nap);
        info.append(delin);
        info.append(this._medLapse);
        info.append(delin);
        info.append(this._disciplineCall);
        info.append(delin);
        info.append(this._assistantID);
        info.append(delin);
        info.append("Empty");
        info.append(delin);
        info.append("Empty");
        info.append(delin);
        info.append("Empty");
        info.append(delin);
        info.append(this._sleepLapse);
        info.append(delin);
        info.append(this._sleepLimit);
        info.append(delin);
        info.append(this._awakeLapse);
        info.append(delin);
        info.append(this._awakeLimit);
        info.append(delin);
        info.append(this._injLength);
        info.append(delin);
        info.append(this._sickLength);
        info.append(delin);
        info.append(this._morningTrain);
        info.append(delin);
        info.append(this._dayTrain);
        info.append(delin);
        info.append(this._nightTrain);
        info.append(delin);
        info.append(this._timeRanks.getFavorite().ordinal());
        info.append(delin);
        info.append(this._day);
        info.append(delin);
        info.append(this._calories);
        info.append(delin);
        info.append(this._perfectWins);
        info.append(delin);
        info.append(this._weightRecord[0]);
        info.append(delin);
        info.append(this._weightRecord[1]);
        info.append(delin);
        info.append(this._weightRecord[2]);
        info.append(delin);
        info.append(this._weightRecord[3]);
        info.append(delin);
        info.append(this._foodRanks.getUnlockedDislike());
        info.append(delin);
        info.append(this._attributeRanks.getUnlockedDislike());
        info.append(delin);
        info.append(this._timeRanks.getUnlockedDislike());
        info.append(delin);
        info.append(this._foodRanks.getUnlockedFav());
        info.append(delin);
        info.append(this._attributeRanks.getUnlockedFav());
        info.append(delin);
        info.append(this._timeRanks.getUnlockedFav());
        info.append(delin);
        info.append(this._foodRanks.getRank(Enum.Food.Meat).getRank());
        info.append(delin);
        info.append(this._foodRanks.getRank(Enum.Food.Veg).getRank());
        info.append(delin);
        info.append(this._foodRanks.getRank(Enum.Food.Fruit).getRank());
        info.append(delin);
        info.append(this._foodRanks.getRank(Enum.Food.Fish).getRank());
        info.append(delin);
        info.append(this._attributeRanks.getRank(Enum.Attribute.Vaccine).getRank());
        info.append(delin);
        info.append(this._attributeRanks.getRank(Enum.Attribute.Data).getRank());
        info.append(delin);
        info.append(this._attributeRanks.getRank(Enum.Attribute.Virus).getRank());
        info.append(delin);
        info.append(this._timeRanks.getRank(Enum.Time.Morning).getRank());
        info.append(delin);
        info.append(this._timeRanks.getRank(Enum.Time.Noon).getRank());
        info.append(delin);
        info.append(this._timeRanks.getRank(Enum.Time.Night).getRank());
        info.append(delin);
        info.append(0);
        info.append(delin);
        info.append(this._clock.getNanoRemainder());
        info.append(delin);
        info.append(this._bits);
        info.append(delin);
        info.append(this._temp);
        info.append(delin);
        info.append(this._dayTemp);
        info.append(delin);
        info.append(this._homeHabitat);
        info.append(delin);
        info.append(this._tempGoal);
        info.append(delin);
        info.append(this._grainEaten);
        info.append(delin);
        info.append(this._dairyEaten);
        info.append(delin);
        info.append(this._itemInterest);
        info.append(delin);
        info.append(this._world.getAdventureLife());
        info.append(delin);
        info.append(this._savedFromDeath);
        info.append(delin);
        info.append(this._hungerDecayLapse);
        info.append(delin);
        info.append(this._isFree);
        info.append(delin);
        info.append(this._settings.isOnTop());
        info.append(delin);
        info.append(this._energyRank);
        info.append(delin);
        info.append(this._weightRank);
        info.append(delin);
        info.append(this._moodRank);
        info.append(delin);
        info.append(this._checksum);
        info.append(delin);
        info.append(this._gameModified);
        info.append(delin);
        info.append(this._meatEaten);
        info.append(delin);
        info.append(this._vegEaten);
        info.append(delin);
        info.append(this._fruitEaten);
        info.append(delin);
        info.append(this._fishEaten);
        info.append(delin);
        info.append(this._junkEaten);
        info.append(delin);
        info.append(this._medEaten);
        info.append(delin);
        info.append(this._battleImmunity);
        info.append(delin);
        info.append(this._napCycle);
        info.append(delin);
        info.append(this._obedienceChangeLapse);
        info.append(delin);
        info.append("Empty");
        info.append(delin);
        info.append("Empty");
        info.append(delin);
        info.append(0);
        info.append(delin);
        info.append(this._settings.isFocus());
        info.append(delin);
        info.append(this._postponeDie);
        info.append(delin);
        info.append(this._postponeEvolve);
        info.append(delin);
        info.append(this._napEnergyInc);
        info.append(delin);
        info.append(System.nanoTime());
        info.append(delin);
        info.append(0);
        info.append(delin);
        info.append(this._moodRecord[0]);
        info.append(delin);
        info.append(this._moodRecord[1]);
        info.append(delin);
        info.append(this._moodRecord[2]);
        info.append(delin);
        info.append(this._moodRecord[3]);
        info.append(delin);
        info.append(this._difficultySetting);
        info.append(delin);
        info.append(this._protein);
        info.append(delin);
        info.append(this._mineral);
        info.append(delin);
        info.append(this._vitamin);
        info.append(delin);
        info.append(this._clock.getMinuteBeforeChange());
        info.append(delin);
        info.append(this._clock.getTimeChanged());
        info.append(delin);
        info.append(this._clock.getAlarmMinutes());
        info.append(delin);
        info.append(this._autoCare);
        info.append(delin);
        info.append(this._tourneyAlarm);
        info.append(delin);
        info.append(0);
        info.append(delin);
        info.append(this._minToDecayHunger);
        info.append(delin);
        info.append((Object)this._xAntibodyState);
        info.append(delin);
        info.append(this._xAntibodyCount);
        info.append(delin);
        info.append(this._fatigueLength);
        info.append(delin);
        info.append(this._strengthDecayLapse);
        info.append(delin);
        info.append(this._minToDecayStrength);
        info.append(delin);
        info.append(this._foodRanks.getRank(Enum.Food.Med).getRank());
        info.append(delin);
        info.append(this._foodRanks.getRank(Enum.Food.Junk).getRank());
        info.append(delin);
        info.append(this._foodRanks.getRank(Enum.Food.Grain).getRank());
        info.append(delin);
        info.append(this._foodRanks.getRank(Enum.Food.Dairy).getRank());
        info.append(delin);
        info.append(this._foodRanks.getRank(Enum.Food.None).getRank());
        info.append(delin);
        info.append(this._timeRanks.getRank(Enum.Time.None).getRank());
        info.append(delin);
        info.append(this._attributeRanks.getRank(Enum.Attribute.None).getRank());
        info.append(delin);
        info.append(this._sleepMinutes);
        info.append(delin);
        info.append(this._dailyMoodRecord[0]);
        info.append(delin);
        info.append(this._dailyMoodRecord[1]);
        info.append(delin);
        info.append(this._dailyMoodRecord[2]);
        info.append(delin);
        info.append(this._dailyMoodRecord[3]);
        save.println(info.toString());
    }

    private void writeMap(PrintWriter save, StringBuilder info, String delin) {
        try {
            info.append(this._world.getEnergyDec());
            info.append(delin);
            info.append(this._world.getStepInc());
            info.append(delin);
            for (int i = 1; i < this._world.getMaps().size(); ++i) {
                MapLevel map = this._world.getMaps().get(i);
                info.append(map.getIsComplete());
                info.append(delin);
                info.append(map.getIsCurrent());
                info.append(delin);
                for (Zone zone : map.getZones()) {
                    if (zone == null) continue;
                    info.append(zone.getCurrentLocation());
                    info.append(delin);
                    info.append(zone.getIsComplete());
                    info.append(delin);
                    info.append(zone.getIsCurrent());
                    info.append(delin);
                    info.append(zone.getIsUnlocked());
                    info.append(delin);
                }
                info.append(map.getIsUnlocked());
                info.append(delin);
            }
            save.println(info.toString());
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
            e.printStackTrace();
        }
    }

    private void writeFoughtTrophiesToday(PrintWriter save, StringBuilder info, String delin) {
        if (!this._foughtTrophiesToday.isEmpty()) {
            for (int i : this._foughtTrophiesToday) {
                info.append(i);
                info.append(delin);
            }
        }
        save.println(info.toString());
    }

    private void readFoughtTrophiesToday(String[] info) {
        if (info.length > 0 && !info[0].isEmpty()) {
            for (int i = 0; i < info.length; ++i) {
                this._foughtTrophiesToday.add(Integer.valueOf(info[i]));
            }
        }
    }

    private void writeTowns(PrintWriter save, StringBuilder info, String delin) {
        for (Town t : this._world.getTowns()) {
            info.append(t.isUnlocked());
            info.append(delin);
        }
        save.println(info.toString());
    }

    private void readTowns(String[] info) {
        if (info.length > 0) {
            ArrayList<Town> towns = this._world.getTowns();
            for (int i = 0; i < info.length; ++i) {
                towns.get(i).setUnlocked(Boolean.parseBoolean(info[i]));
            }
        }
    }

    private void writeTrophies(PrintWriter save, StringBuilder info, String delin) {
        try {
            for (Trophy t : this._tournament.getTrophies()) {
                if (!t.getEarned()) continue;
                info.append(t.getID()).append(";").append(t.getSeasonBeat());
                info.append(delin);
            }
            save.println(info.toString());
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
        }
    }

    private void writeDailyTrophies(PrintWriter save, StringBuilder info, String delin) {
        try {
            for (int i : this._dailyTrophies) {
                info.append(i);
                info.append(delin);
            }
            save.println(info.toString());
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
        }
    }

    private void writeTrophySchedule(PrintWriter save, StringBuilder info, String delin) {
        try {
            for (int i : this._trophySchedule) {
                info.append(i);
                info.append(delin);
            }
            save.println(info.toString());
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
        }
    }

    private void writeFoods(PrintWriter save, StringBuilder info, String delin) {
        try {
            for (FoodType food : this._foodTypes) {
                String f = food.getID() + "q" + food.getCurrentUses() + "su" + food.getShopUnlocked();
                info.append(f);
                info.append(delin);
            }
            save.println(info.toString());
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
        }
    }

    private void writeHabitatRecord(PrintWriter save, StringBuilder info, String delin) {
        for (int i : this._habitatRecord) {
            info.append(i);
            info.append(delin);
        }
        save.println(info.toString());
    }

    private void writeTempRecord(PrintWriter save, StringBuilder info, String delin) {
        try {
            for (int temp : this._tempRecord) {
                info.append(temp);
                info.append(delin);
            }
            save.println(info.toString());
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
        }
    }

    private void writeObedienceRecord(PrintWriter save, StringBuilder info, String delin) {
        try {
            for (int i : this._obedienceRecord) {
                info.append(i);
                info.append(delin);
            }
            save.println(info.toString());
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
        }
    }

    private void writeCooldown(PrintWriter save, StringBuilder info, String delin) {
        ArrayList<Enemy> enemies = this._world.getEnemies();
        try {
            for (int i = 0; i < enemies.size(); ++i) {
                if (enemies.get(i).getCooldown() <= 0) continue;
                info.append(i).append(":").append(enemies.get(i).getCooldown());
                info.append(delin);
            }
            save.println(info.toString());
        }
        catch (NullPointerException e) {
            CrashEntry.generateEntry(e);
        }
    }

    private void writeHabitats(PrintWriter save, StringBuilder info, String delin) {
        try {
            for (Habitat habitat : this._habitats) {
                info.append(habitat.getUnlocked());
                info.append(delin);
            }
            save.println(info.toString());
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
        }
    }

    private void writeItems(PrintWriter save, StringBuilder info, String delin) {
        try {
            for (Item item : this._items) {
                String i = item.getID() + "o" + item.getShopUnlocked() + "q" + item.getCurrentUses();
                info.append(i);
                info.append(delin);
            }
            save.println(info.toString());
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
        }
    }

    private void writeDigimemory(PrintWriter save, StringBuilder info, String delin) {
        try {
            Item mem = this.getDigimemory();
            info.append(mem._vaccine);
            info.append(delin);
            info.append(mem._data);
            info.append(delin);
            info.append(mem._virus);
            info.append(delin);
            info.append(mem._seconds);
            info.append(delin);
            info.append(mem._description);
            info.append(delin);
            info.append(mem._details);
            info.append(delin);
            info.append(mem.getCurrentUses());
            save.println(info.toString());
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
        }
    }

    private void readDigimemory(String[] info) {
        try {
            Item mem = this.getDigimemory();
            mem._vaccine = Integer.parseInt(info[0]);
            mem._data = Integer.parseInt(info[1]);
            mem._virus = Integer.parseInt(info[2]);
            mem._seconds = Integer.parseInt(info[3]);
            mem._description = info[4];
            mem._details = info[5];
            mem.setCurrentUses(Integer.parseInt(info[6]));
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
        }
    }

    private void writeEvolutionHistory(PrintWriter save, StringBuilder info, String delin) {
        try {
            for (int[] digimon : this._evolHistory) {
                info.append(digimon[0]).append("j").append(digimon[1]);
                info.append(delin);
            }
            save.println(info.toString());
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
            e.printStackTrace();
        }
    }

    private void writeGenerationHistory(PrintWriter save, StringBuilder info, String delin) {
        try {
            for (ArrayList<int[]> a : this._generationHistory) {
                for (int[] s : a) {
                    if (s[0] == -1) continue;
                    info.append(s[0]).append("j").append(s[1]);
                    info.append(":");
                }
                info.append(delin);
            }
            save.println(info.toString());
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
        }
    }

    private void readGenerationHistory(String[] info) {
        try {
            for (String s : info) {
                if (s.isEmpty()) continue;
                String[] g = s.split(":");
                ArrayList<int[]> gi = new ArrayList<int[]>();
                try {
                    for (int i = 0; i < g.length; ++i) {
                        String[] a = g[i].split("j");
                        gi.add(new int[]{Integer.parseInt(a[0]), a.length > 1 ? Integer.parseInt(a[1]) : -1});
                    }
                }
                catch (NumberFormatException exc) {
                    gi.add(new int[]{this._evolution.getDigimon(g[0]).getIndex(), -1});
                    gi.add(new int[]{Integer.parseInt(g[1], -1)});
                    for (int i = 2; i < g.length; ++i) {
                        gi.add(new int[]{this._evolution.getDigimon(g[i]).getIndex(), -1});
                    }
                }
                this._generationHistory.add(gi);
            }
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
        }
    }

    private void writeDNA(PrintWriter save, StringBuilder info, String delin) {
        try {
            for (int i : this._dna.getDNA()) {
                info.append(i);
                info.append(delin);
            }
            for (int i : this._dna.getOwned()) {
                info.append(i);
                info.append(delin);
            }
            save.println(info.toString());
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
        }
    }

    private void readDNA(String[] info) {
        try {
            this._dna.readInfo(info);
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
            e.printStackTrace();
        }
    }

    private void writeDailyShopTrophies(PrintWriter save, StringBuilder info, String delin) {
        try {
            String i = "";
            for (ShopConsumable f : this._homeFoodShop) {
                i = i + f.getConsumableID() + "q" + f.getCurrentStock() + "q" + f.getSalePrice() + ";";
            }
            i = i + ":";
            for (ShopConsumable item : this._homeItemShop) {
                i = i + item.getConsumableID() + "q" + item.getCurrentStock() + "q" + item.getSalePrice() + ";";
            }
            info.append(i);
            info.append(delin);
            for (MapLevel m : this._world.getMaps()) {
                i = "";
                for (Zone z : m.getZones()) {
                    for (Town t : z.getTowns()) {
                        i = i + "m" + m.getMapNum() + ":" + z.getZoneNum() + ":" + t.getID() + "d";
                        if (!t.getFoodShop().isEmpty()) {
                            for (ShopConsumable f : t.getFoodShop(this)) {
                                i = i + f.getID() + ":" + f.getConsumableID() + ":" + f.getCurrentStock() + ":" + f.getSalePrice() + ";";
                            }
                        }
                        i = i + "d";
                        if (!t.getItemShop().isEmpty()) {
                            for (ShopConsumable item : t.getItemShop(this)) {
                                i = i + item.getID() + ":" + item.getConsumableID() + ":" + item.getCurrentStock() + ":" + item.getSalePrice() + ";";
                            }
                        }
                        i = i + "d";
                        if (t.getTrophies() == null || t.getTrophies().length <= 0) continue;
                        for (Object troph : (Object)t.getTrophies(this)) {
                            i = i + (int)troph + ";";
                        }
                    }
                }
                info.append(i);
                info.append(delin);
            }
            save.println(info.toString());
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
        }
    }

    private void readDailyShopTrophies(String[] info) {
        try {
            String[] home = info[0].split(":");
            if (home.length > 0) {
                int salePrice;
                int quantity;
                int id;
                String[] foods;
                for (String s : foods = home[0].split(";")) {
                    String[] data = s.split("q");
                    id = Integer.parseInt(data[0]);
                    quantity = data.length > 1 ? Integer.parseInt(data[1]) : -1;
                    salePrice = data.length > 2 ? Integer.parseInt(data[2]) : 0;
                    ShopConsumable c = this._foodTypes.get(id).getHomeShop();
                    c.setCurrentStock(quantity);
                    c.setSalePrice(salePrice);
                    this._homeFoodShop.add(c);
                }
                if (home.length > 1) {
                    String[] items;
                    for (String s : items = home[1].split(";")) {
                        String[] data = s.split("q");
                        id = Integer.parseInt(data[0]);
                        quantity = data.length > 1 ? Integer.parseInt(data[1]) : -1;
                        salePrice = data.length > 2 ? Integer.parseInt(data[2]) : 0;
                        ShopConsumable c = this._items.get(id).getHomeShop();
                        c.setCurrentStock(quantity);
                        c.setSalePrice(salePrice);
                        this._homeItemShop.add(c);
                    }
                }
            }
            for (int i = 1; i < info.length; ++i) {
                String[] mapInfo;
                for (String innerZone : mapInfo = info[i].split("m")) {
                    ShopConsumable override;
                    ShopConsumable c;
                    int salePrice;
                    int quantity;
                    int consumable;
                    if (innerZone.isEmpty()) continue;
                    String[] zoneInfo = innerZone.split("d");
                    String[] idInfo = zoneInfo[0].split(":");
                    String[] foodInfo = null;
                    String[] itemInfo = null;
                    String[] trophyInfo = null;
                    if (zoneInfo.length > 1) {
                        foodInfo = zoneInfo[1].split(";");
                    }
                    if (zoneInfo.length > 2) {
                        itemInfo = zoneInfo[2].split(";");
                    }
                    if (zoneInfo.length > 3) {
                        trophyInfo = zoneInfo[3].split(";");
                    }
                    int mapNum = idInfo.length > 0 ? Integer.parseInt(idInfo[0]) : -1;
                    int zoneNum = idInfo.length > 1 ? Integer.parseInt(idInfo[1]) : -1;
                    int townNum = idInfo.length > 2 ? Integer.parseInt(idInfo[2]) : -1;
                    Zone zone = null;
                    Town town = null;
                    for (MapLevel m : this._world.getMaps()) {
                        if (mapNum == m.getMapNum()) {
                            for (Zone z : m.getZones()) {
                                for (Town t : z.getTowns()) {
                                    if (t.getID() != townNum) continue;
                                    town = t;
                                    break;
                                }
                                if (z.getZoneNum() != zoneNum) continue;
                                zone = z;
                                break;
                            }
                        }
                        if (zone == null) continue;
                        break;
                    }
                    if (town == null) continue;
                    try {
                        if (foodInfo != null && foodInfo.length > 0) {
                            for (String s : foodInfo) {
                                if (s.isEmpty()) continue;
                                String[] food = s.split(":");
                                int id = Integer.parseInt(food[0]);
                                consumable = Integer.parseInt(food[1]);
                                quantity = Integer.parseInt(food[2]);
                                int n = salePrice = food.length > 3 ? Integer.parseInt(food[3]) : 0;
                                if (id == -1) {
                                    c = this._foodTypes.get(consumable).getHomeShop();
                                } else {
                                    override = town.getOverrideFood(id);
                                    c = new ShopConsumable(override.getID(), override.getConsumableID(), override.isFood(), override.getStockChance(), override.getMaxStock(), override.getMinStock(), override.getTimeAvailable(), override.getPrice(), override.mustStock(), override.getSaleChance(), override.getSaleFactor(), override.getResellFactor());
                                }
                                c.setCurrentStock(quantity);
                                c.setSalePrice(salePrice);
                                town.getFoodShop().add(c);
                            }
                        }
                    }
                    catch (IndexOutOfBoundsException e) {
                        CrashEntry.generateEntry(e);
                    }
                    try {
                        if (itemInfo != null && itemInfo.length > 0) {
                            for (String s : itemInfo) {
                                if (s.isEmpty()) continue;
                                String[] item = s.split(":");
                                int id = Integer.parseInt(item[0]);
                                consumable = Integer.parseInt(item[1]);
                                quantity = Integer.parseInt(item[2]);
                                int n = salePrice = item.length > 3 ? Integer.parseInt(item[3]) : 0;
                                if (id == -1) {
                                    c = this._items.get(consumable).getHomeShop();
                                } else {
                                    override = town.getOverrideItem(id);
                                    c = new ShopConsumable(override.getID(), override.getConsumableID(), override.isFood(), override.getStockChance(), override.getMaxStock(), override.getMinStock(), override.getTimeAvailable(), override.getPrice(), override.mustStock(), override.getSaleChance(), override.getSaleFactor(), override.getResellFactor());
                                }
                                c.setCurrentStock(quantity);
                                c.setSalePrice(salePrice);
                                town.getItemShop().add(c);
                            }
                        }
                    }
                    catch (IndexOutOfBoundsException e) {
                        CrashEntry.generateEntry(e);
                    }
                    try {
                        if (trophyInfo == null || trophyInfo.length <= 0) continue;
                        int[] t = new int[trophyInfo.length];
                        for (int index = 0; index < t.length; ++index) {
                            t[index] = Integer.parseInt(trophyInfo[index]);
                        }
                        town.setTrophies(t);
                    }
                    catch (IndexOutOfBoundsException e) {
                        CrashEntry.generateEntry(e);
                    }
                }
            }
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
            e.printStackTrace();
        }
    }

    private void writeTournament(PrintWriter save, StringBuilder info, String delin) {
        info.append(this._tournament.getActive());
        if (this._tournament.getActive()) {
            info.append(delin);
            info.append(this._tournament.getCurrentTrophy().getID());
            info.append(delin);
            info.append(this._tournament.getBits());
        }
        save.println(info.toString());
    }

    private void readTournament(String[] info) {
        try {
            if (Boolean.parseBoolean(info[0])) {
                Trophy t = this._tournament.getTrophy(Integer.parseInt(info[1]));
                this._tournament.setCurrentTrophy(t);
                this._tournament.setActive(true);
                this._tournament.setBits(Integer.parseInt(info[2]));
            }
        }
        catch (ArrayIndexOutOfBoundsException e) {
            CrashEntry.generateEntry(e);
        }
    }

    private void writeTournamentRoster(PrintWriter save, StringBuilder info, String delin) {
        if (this._tournament.getActive()) {
            for (Enemy e : this._tournament.getRoster()) {
                if (e != null) {
                    info.append((Object)e.getOppAttribute());
                    info.append(delin);
                    info.append((Object)e.getOppField());
                    info.append(delin);
                    info.append((Object)e.getOppElement());
                    info.append(delin);
                    info.append((Object)e.getOppStage());
                    info.append(delin);
                    info.append(e.getSpriteNum());
                    info.append(delin);
                    info.append(e.getSpriteSet());
                    info.append(delin);
                    info.append(e.getIndex());
                    info.append(delin);
                    info.append(e.getEnemyHealth());
                    info.append(delin);
                    info.append(e.getOppYellow());
                    info.append(delin);
                    info.append(e.getOppRed());
                    info.append(delin);
                    info.append(e.getOppGreen());
                    info.append(";");
                    continue;
                }
                info.append("null;");
            }
        }
        save.println(info.toString());
    }

    private void readTournamentRoster(String info) {
        if (this._tournament.getActive()) {
            String[] enemies;
            ArrayList<Enemy> roster = new ArrayList<Enemy>();
            for (String l : enemies = info.split(";")) {
                String[] details = l.split(",");
                if (details[0].equals("null")) {
                    roster.add(null);
                    continue;
                }
                Enemy e = new Enemy();
                e.setOppAttribute(Enum.Attribute.valueOf(details[0]));
                e.setOppField(Enum.Field.valueOf(details[1]));
                e.setOppElement(Enum.Element.valueOf(details[2]));
                e.setOppStage(Enum.Stage.valueOf(details[3]));
                e.setSpriteNum(Integer.parseInt(details[4]));
                e.setSpriteSet(Integer.parseInt(details[5]));
                e.setIndex(Integer.parseInt(details[6]));
                e.setEnemyHealth(Integer.parseInt(details[7]));
                e.setOppGreen(Integer.parseInt(details[8]));
                e.setOppYellow(Integer.parseInt(details[9]));
                e.setOppRed(Integer.parseInt(details[10]));
                roster.add(e);
            }
            this._tournament.setRoster(roster.toArray(new Enemy[roster.size()]));
        }
    }

    private void writeTournamentDisqualified(PrintWriter save, StringBuilder info, String delin) {
        if (this._tournament.getActive()) {
            for (Enemy e : this._tournament.getDisqualified()) {
                info.append(this._tournament.getEnemyIndex(e));
                info.append(delin);
            }
        }
        save.println(info.toString());
    }

    private void readTournamentDisqualified(String[] info) {
        if (this._tournament.getActive()) {
            ArrayList<Enemy> e = this._tournament.getDisqualified();
            e.clear();
            for (String s : info) {
                if (Utility.isBlank(s)) continue;
                e.add(this._tournament.getRoster()[Integer.parseInt(s)]);
            }
        }
    }

    private void writeTournamentChecked(PrintWriter save, StringBuilder info, String delin) {
        if (this._tournament.getActive()) {
            for (Enemy e : this._tournament.getChecked()) {
                info.append(this._tournament.getEnemyIndex(e));
                info.append(delin);
            }
        }
        save.println(info.toString());
    }

    private void readTournamentChecked(String[] info) {
        if (this._tournament.getActive()) {
            ArrayList<Enemy> e = this._tournament.getChecked();
            e.clear();
            for (String s : info) {
                if (Utility.isBlank(s)) continue;
                e.add(this._tournament.getRoster()[Integer.parseInt(s)]);
            }
        }
    }

    private void writeLevelsFought(PrintWriter save, StringBuilder info, String delin) {
        for (int i : this._levelsFought) {
            info.append(i);
            info.append(delin);
        }
        save.println(info.toString());
    }

    private void readLevelsFought(String[] info) {
        if (info.length > 0) {
            try {
                for (String s : info) {
                    this._levelsFought.add(Integer.parseInt(s));
                }
            }
            catch (NumberFormatException numberFormatException) {
            }
            catch (Exception ex) {
                CrashEntry.generateEntry(ex);
            }
        }
    }

    private void writeWeather(PrintWriter save, StringBuilder info, String delin) {
        MapLevel map = this._world.getCurrentMap();
        Zone zone = this._world.getCurrentZone();
        this.addCurrentWeatherToRecord(this.getExistingWeatherRecord(map, zone), map, zone);
        for (WeatherRecord w : this._weatherRecord) {
            info.append(w.writeInfo());
            info.append(delin);
        }
        save.println(info.toString());
    }

    private void readWeather(String[] info) {
        for (String s : info) {
            if (Utility.isBlank(s)) continue;
            WeatherRecord w = new WeatherRecord(s.split(";"));
            this._weatherRecord.add(w);
        }
    }

    private void writeConsumableEffects(PrintWriter save, StringBuilder info, String delin) {
        for (CareEffect e : this._careEffects) {
            info.append(e.getLapse());
            info.append(delin);
        }
        save.println(info.toString());
    }

    private void readConsumableEffects(String[] info) {
        for (int i = 0; i < info.length; ++i) {
            String s = info[i];
            if (Utility.isBlank(s)) continue;
            this._careEffects.get(i).setLapse(Integer.parseInt(s));
        }
    }

    private void saveTree() {
        this.loadTree();
        File saveFile = new File("files" + File.separator + "saves" + File.separator + "Shared" + File.separator + "tree.txt");
        if (!saveFile.exists()) {
            try {
                if (!saveFile.getParentFile().exists()) {
                    saveFile.getParentFile().mkdirs();
                }
                if (!saveFile.exists()) {
                    saveFile.createNewFile();
                }
            }
            catch (IOException e) {
                e.printStackTrace();
            }
        }
        try (PrintWriter save = new PrintWriter(saveFile);){
            String s = "";
            for (EvolutionInfo e : this._evolution.getEvolDigimon()) {
                if (e.getIsNatural()) continue;
                Boolean unlocked = e.getUnlocked();
                s = s + unlocked + ",";
            }
            save.append(s);
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
            e.printStackTrace();
        }
    }

    public synchronized void autoSave() {
        if (!this._saving && this._saveString != null && !this._tournament.getActive() && Config._autoSave) {
            Thread t = new Thread("autosave"){

                @Override
                public void run() {
                    PhysicalState.this.save(true, false);
                }
            };
            t.start();
        }
    }

    public void checkLoadType() {
        this.load();
        this.testData();
    }

    private void testData() {
    }

    public void setDigimon(EvolutionInfo e, boolean recordGeneration) {
        this.resetDigimon(recordGeneration);
        this._evolution.digivolve(e, this, this._evolution.getEvolDigimon(), false, -1);
    }

    private void evolTest(String digimon) {
        this.evolTest(this._evolution.getDigimon(digimon));
    }

    private void evolTest(int id) {
        this.evolTest(this._evolution.getDigimon(id));
    }

    private void evolTest(EvolutionInfo e) {
        this._alive = true;
        this._evolution.digivolve(e, this, this._evolution.getEvolDigimon(), false, -1);
        this._growthPeriod = 950400L;
        this._totalLifespan = 1296000L;
        this._lapsedLife = 864000L;
        this._bonus = 10;
        this._dataPower = 300;
        this._vaccinePower = 300;
        this._virusPower = 300;
        this._overeat = 1;
        this._disturb = 0;
        this._sickCount = 0;
        this._injCount = 0;
        this._energy = (byte)24;
        this._fullHealthPoints = (byte)30;
        this._dayTrain = 0;
        this._morningTrain = 0;
        this._nightTrain = 99;
        this._habitatRecord[2] = 0;
        this._dna.resetDNA();
        this._dna.setDNA(Enum.Field.DeepSaver, 1);
        this._battles = 31;
        this._wins = 31;
        this._perfectWins = 0;
        this._mistake = 0;
        for (int i = 0; i < 25; ++i) {
            this._levelsFought.add(3);
        }
        this._obedienceRecord[0] = 10;
        this._obedienceRecord[1] = 1000;
        this._moodRecord[0] = 500;
        this._weightRecord[2] = 500;
    }

    private void jogressTest(String s) {
        this._evolution.digivolve(this._evolution.getDigimon(s), this, this._evolution.getEvolDigimon(), false, -1);
        this._dataPower = 46;
        this._vaccinePower = 131;
        this._virusPower = 0;
        this._overeat = 2;
        this._disturb = 0;
        this._energy = (byte)24;
        this._fullHealthPoints = (byte)30;
        this._dayTrain = 0;
        this._nightTrain = 0;
        this._morningTrain = 221;
        this.setMood(180);
        this._dna.resetDNA();
        this._battles = 60;
        this._wins = 50;
        this._mistake = 0;
        this._obedience = Config._maxObedience;
        this._obedienceRecord[0] = 10;
        this._obedienceRecord[1] = 1000;
        this._tempRecord[0] = 1;
        this._tempRecord[1] = 5;
        this._moodRecord[0] = 100;
        this._growthPeriod = 1000L;
        for (int i = 0; i < 11; ++i) {
            this._levelsFought.add(2);
        }
        this._totalLifespan = this._growthPeriod + 100000L;
        this._lapsedLife = this._growthPeriod - 1000L;
    }

    private void load() {
        this._loading = true;
        this._canEvolveOrDie = true;
        String save = "files" + File.separator + "saves" + File.separator + this._saveString;
        try {
            ArrayList<String> lines = Cryption.decrypt("hackero/", save);
            this.readInfo(lines.get(0).split(","));
            this.readMap(lines.get(1).split(","));
            this.readTrophies(lines.get(2).split(","));
            this.readDailyTrophies(lines.get(3).split(","));
            this.readTrophySchedule(lines.get(4).split(","));
            this.readFoods(lines.get(5).split(","));
            this.readTempRecord(lines.get(6).split(","));
            this.readHabitats(lines.get(7).split(","));
            this.readItems(lines.get(8).split(","));
            this.readDailyShopTrophies(lines.get(9).split(","));
            this.readDigimemory(lines.get(10).split(","));
            this.readGenerationHistory(lines.get(11).split(","));
            this.readDNA(lines.get(12).split(","));
            this.readHabitatRecord(lines.get(13).split(","));
            this.readObedienceRecord(lines.get(14).split(","));
            this.readCooldown(lines.get(15).split(","));
            this.readEvolutionHistory(lines.get(16).split(","));
            this.readTournament(lines.get(17).split(","));
            this.readTournamentRoster(lines.get(18));
            this.readTournamentChecked(lines.get(19).split(","));
            this.readTournamentDisqualified(lines.get(20).split(","));
            this.readLevelsFought(lines.get(21).split(","));
            this.readWeather(lines.get(22).split(","));
            this.readConsumableEffects(lines.get(23).split(","));
            this.readTowns(lines.get(24).split(","));
            this.readFoughtTrophiesToday(lines.get(25).split(","));
        }
        catch (Exception e) {
            if (!this._tournamentVersion) {
                this.oldLoad(save);
            }
            CrashEntry.generateEntry(e);
        }
        this.loadCurrentHabitat();
        this.loadTree();
        if (this._timeSkip && this._clock.getFastMod() == 1) {
            this.timeSkip();
        }
        try {
            if (!this._gameModified && this._checksum != null) {
                this._gameModified = !this._checksum.equals(Checksum.generate());
            }
        }
        catch (Exception exception) {
            // empty catch block
        }
        this._loading = false;
    }

    private void oldLoad(String save) {
        try (FileReader in = new FileReader(save);
             BufferedReader reader = new BufferedReader(in);){
            this.readInfo(reader.readLine().split(","));
            this.readMap(reader.readLine().split(","));
            this.readTrophies(reader.readLine().split(","));
            this.readDailyTrophies(reader.readLine().split(","));
            this.readTrophySchedule(reader.readLine().split(","));
            this.readFoods(reader.readLine().split(","));
            this.readTempRecord(reader.readLine().split(","));
            this.readHabitats(reader.readLine().split(","));
            this.readItems(reader.readLine().split(","));
            this.readDailyShopTrophies(reader.readLine().split(","));
            this.readDigimemory(reader.readLine().split(","));
            this.readGenerationHistory(reader.readLine().split(","));
            this.readDNA(reader.readLine().split(","));
            this.readHabitatRecord(reader.readLine().split(","));
            this.readObedienceRecord(reader.readLine().split(","));
            this.readCooldown(reader.readLine().split(","));
            this.readEvolutionHistory(reader.readLine().split(","));
            this.readTournament(reader.readLine().split(","));
            this.readTournamentRoster(reader.readLine());
            this.readTournamentChecked(reader.readLine().split(","));
            this.readTournamentDisqualified(reader.readLine().split(","));
            this.readLevelsFought(reader.readLine().split(","));
            this.readWeather(reader.readLine().split(","));
            this.readConsumableEffects(reader.readLine().split(","));
            this.readTowns(reader.readLine().split(","));
            this.readFoughtTrophiesToday(reader.readLine().split(","));
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
            e.printStackTrace();
        }
    }

    public void initConfigVariables() {
        this._foodRanks = new Taste<Enum.Food>(Enum.Food.values(), Config._validLikedFood, Config._validDislikedFood, Enum.Food.None);
        this._timeRanks = new Taste<Enum.Time>(Enum.Time.values(), Config._validLikedTime, Config._validDislikedTime, Enum.Time.None);
        this._attributeRanks = new Taste<Enum.Attribute>(Enum.Attribute.values(), Config._validLikedAttribute, Config._validDislikedAttribute, Enum.Attribute.None);
        this._trophySchedule = new int[Config._homeTournamentLimit];
    }

    private void readInfo(String[] info) {
        byte _seconds = 0;
        byte _minutes = 0;
        byte _hours = 0;
        try {
            this._difficultySetting = Integer.parseInt(info[152]);
        }
        catch (Exception e) {
            this._difficultySetting = 0;
        }
        Config.loadConfig(this._difficultySetting, this.MOD_FOLDER, this._tournamentVersion);
        this.initConfigVariables();
        try {
            _seconds = Byte.parseByte(info[0]);
            _minutes = Byte.parseByte(info[1]);
            _hours = Byte.parseByte(info[2]);
            int _fastMod = Integer.parseInt(info[3]);
            switch (_fastMod) {
                case 5: {
                    this._clock.setFastMod(2, true);
                    break;
                }
                case 10: {
                    this._clock.setFastMod(3, true);
                    break;
                }
                case 25: {
                    this._clock.setFastMod(4, true);
                    break;
                }
                default: {
                    this._clock.setFastMod(_fastMod, true);
                }
            }
            this._settings.setShell(Integer.parseInt(info[4]));
            this._settings.setGameScale(Double.parseDouble(info[5]));
            this._settings.setSound(Boolean.parseBoolean(info[6]));
            this._calorieMaxMod = Integer.parseInt(info[7]);
            this._calorieMinMod = Integer.parseInt(info[8]);
            try {
                this._itemInterestLapse = Byte.parseByte(info[9]);
            }
            catch (Exception exception) {
                // empty catch block
            }
            try {
                this._foodRanks.setDisliked(Enum.Food.values()[Integer.parseInt(info[10])]);
                this._attributeRanks.setDisliked(Enum.Attribute.values()[Integer.parseInt(info[11])]);
                this._timeRanks.setDisliked(Enum.Time.values()[Integer.parseInt(info[12])]);
            }
            catch (Exception exception) {
                // empty catch block
            }
            int favFood = Integer.parseInt(info[13]);
            this._foodRanks.setFavorite(Enum.Food.values()[favFood]);
            int favAtt = Integer.parseInt(info[14]);
            this._attributeRanks.setFavorite(Enum.Attribute.values()[favAtt]);
            this._praiseWindow = Byte.parseByte(info[15]);
            this._praise = Boolean.parseBoolean(info[16]);
            this._scoldWindow = Byte.parseByte(info[17]);
            this._scold = Boolean.parseBoolean(info[18]);
            this._refused = Boolean.parseBoolean(info[19]);
            this._mood = Integer.parseInt(info[20]);
            int currentMood = Integer.parseInt(info[21]);
            this._currentMood = Enum.Mood.values()[currentMood];
            this._enthusiasm = Byte.parseByte(info[22]);
            this._obedience = Integer.parseInt(info[23]);
            this._glutton = Byte.parseByte(info[24]);
            this._restless = Byte.parseByte(info[25]);
            this._disposition = Byte.parseByte(info[26]);
            try {
                this._lightsOffMistake = Boolean.parseBoolean(info[27]);
            }
            catch (Exception exception) {
                // empty catch block
            }
            this._timeSkip = Boolean.parseBoolean(info[28]);
            try {
                this._healthPoints = Byte.parseByte(info[29]);
            }
            catch (Exception exception) {
                // empty catch block
            }
            try {
                this._index = Integer.parseInt(info[30]);
            }
            catch (NumberFormatException e) {
                for (int i = 0; i < this._evolution.getEvolDigimon().size(); ++i) {
                    if (!this._evolution.getEvolDigimon().get(i).getName().equals(info[30])) continue;
                    this._index = i;
                    break;
                }
            }
            this._age = Integer.parseInt(info[31]);
            this._bonus = Integer.parseInt(info[32]);
            this._timeToAge = Integer.parseInt(info[33]);
            this._callMinutesPoop = Integer.parseInt(info[34]);
            try {
                this._toiletTrained = Byte.parseByte(info[35]);
            }
            catch (Exception e) {
                // empty catch block
            }
            this._hunger = Byte.parseByte(info[36]);
            this._exercise = Byte.parseByte(info[37]);
            this._energy = Byte.parseByte(info[38]);
            this._weight = Integer.parseInt(info[39]);
            try {
                this._restock = Byte.parseByte(info[40]);
            }
            catch (NumberFormatException e) {
                // empty catch block
            }
            this._fullHealthPoints = Byte.parseByte(info[41]);
            int attribute = Integer.parseInt(info[42]);
            this._attribute = Enum.Attribute.values()[attribute];
            this._vaccinePower = Integer.parseInt(info[43]);
            this._dataPower = Integer.parseInt(info[44]);
            this._virusPower = Integer.parseInt(info[45]);
            this._battles = Integer.parseInt(info[46]);
            this._wins = Integer.parseInt(info[47]);
            this._totalLifespan = Long.parseLong(info[48]);
            this._lapsedLife = Long.parseLong(info[49]);
            this._growthPeriod = Long.parseLong(info[51]);
            this._alive = Boolean.parseBoolean(info[52]);
            int overweight = Integer.parseInt(info[53]);
            this._overweight = Enum.Weight.values()[overweight];
            this._disturb = Integer.parseInt(info[54]);
            this._overeat = Integer.parseInt(info[55]);
            this._mistake = Integer.parseInt(info[56]);
            this._mistakeDay = Integer.parseInt(info[57]);
            String[] filth = info[58].split(":");
            for (int i = 0; i < filth.length; ++i) {
                this._filth[i] = Byte.parseByte(filth[i]);
            }
            this._bmGauge = Integer.parseInt(info[59]);
            this._asleep = Boolean.parseBoolean(info[60]);
            this._lights = Boolean.parseBoolean(info[61]);
            try {
                this._callMinutesHunger = Integer.parseInt(info[62]);
            }
            catch (Exception i) {
                // empty catch block
            }
            try {
                this._callMinutesStrength = Integer.parseInt(info[63]);
            }
            catch (Exception i) {
                // empty catch block
            }
            this._sickCount = Integer.parseInt(info[64]);
            this._injCount = Integer.parseInt(info[65]);
            this._vitaminLapse = Byte.parseByte(info[66]);
            try {
                this._callMinutesLights = Integer.parseInt(info[67]);
            }
            catch (Exception i) {
                // empty catch block
            }
            this._bandageLapse = Byte.parseByte(info[68]);
            try {
                this._callMinutesDiscipline = Integer.parseInt(info[69]);
            }
            catch (Exception i) {
                // empty catch block
            }
            this._nap = Boolean.parseBoolean(info[70]);
            this._medLapse = Byte.parseByte(info[71]);
            this._disciplineCall = Boolean.parseBoolean(info[72]);
            try {
                this._assistantID = Integer.parseInt(info[73]);
            }
            catch (NumberFormatException i) {
                // empty catch block
            }
            this._sleepLapse = Integer.parseInt(info[77]);
            this._sleepLimit = Integer.parseInt(info[78]);
            this._awakeLapse = Integer.parseInt(info[79]);
            this._awakeLimit = Integer.parseInt(info[80]);
            try {
                this._injLength = Byte.parseByte(info[81]);
                this._sickLength = Byte.parseByte(info[82]);
            }
            catch (Exception i) {
                // empty catch block
            }
            this._morningTrain = Integer.parseInt(info[83]);
            this._dayTrain = Integer.parseInt(info[84]);
            this._nightTrain = Integer.parseInt(info[85]);
            int favTime = Integer.parseInt(info[86]);
            this._timeRanks.setFavorite(Enum.Time.values()[favTime]);
            this._day = Integer.parseInt(info[87]);
            this._calories = Integer.parseInt(info[88]);
            this._perfectWins = Integer.parseInt(info[89]);
            try {
                this._weightRecord[0] = Integer.parseInt(info[90]);
                this._weightRecord[1] = Integer.parseInt(info[91]);
                this._weightRecord[2] = Integer.parseInt(info[92]);
                this._weightRecord[3] = Integer.parseInt(info[93]);
            }
            catch (Exception e) {
                int evol = 0;
                int i = 90;
                while (evol < 7) {
                    if (!info[i].isEmpty()) {
                        this._evolHistory.add(new int[]{this._evolution.getDigimon(info[i]).getIndex(), -1});
                    }
                    ++evol;
                    ++i;
                }
            }
            this._foodRanks.setUnlockedDislike(Boolean.parseBoolean(info[94]));
            this._attributeRanks.setUnlockedDislike(Boolean.parseBoolean(info[95]));
            this._timeRanks.setUnlockedDislike(Boolean.parseBoolean(info[96]));
            this._foodRanks.setUnlockedFav(Boolean.parseBoolean(info[97]));
            this._attributeRanks.setUnlockedFav(Boolean.parseBoolean(info[98]));
            this._timeRanks.setUnlockedFav(Boolean.parseBoolean(info[99]));
            this._foodRanks.getRank(Enum.Food.Meat).setRank(Integer.parseInt(info[100]));
            this._foodRanks.getRank(Enum.Food.Veg).setRank(Integer.parseInt(info[101]));
            this._foodRanks.getRank(Enum.Food.Fruit).setRank(Integer.parseInt(info[102]));
            this._foodRanks.getRank(Enum.Food.Fish).setRank(Integer.parseInt(info[103]));
            this._attributeRanks.getRank(Enum.Attribute.Vaccine).setRank(Integer.parseInt(info[104]));
            this._attributeRanks.getRank(Enum.Attribute.Data).setRank(Integer.parseInt(info[105]));
            this._attributeRanks.getRank(Enum.Attribute.Virus).setRank(Integer.parseInt(info[106]));
            this._timeRanks.getRank(Enum.Time.Morning).setRank(Integer.parseInt(info[107]));
            this._timeRanks.getRank(Enum.Time.Noon).setRank(Integer.parseInt(info[108]));
            this._timeRanks.getRank(Enum.Time.Night).setRank(Integer.parseInt(info[109]));
            this._currentWeather = Enum.Weather.Clear;
            long nR = Integer.parseInt(info[111]);
            this._clock.setNanoRemainder(nR, true, this);
            this._bits = Integer.parseInt(info[112]);
            this._temp = Byte.parseByte(info[113]);
            this._dayTemp = Byte.parseByte(info[114]);
            this._homeHabitat = Integer.parseInt(info[115]);
            this._tempGoal = Byte.parseByte(info[116]);
            try {
                this._grainEaten = Integer.parseInt(info[117]);
                this._dairyEaten = Integer.parseInt(info[118]);
            }
            catch (Exception exception) {
                // empty catch block
            }
            this._itemInterest = Byte.parseByte(info[119]);
            this._world.setRawLife(Byte.parseByte(info[120]));
            this._savedFromDeath = Byte.parseByte(info[121]);
            this._hungerDecayLapse = Byte.parseByte(info[122]);
            this._isFree = Boolean.parseBoolean(info[123]);
            this._settings.setOnTop(Boolean.parseBoolean(info[124]));
            this._energyRank = Integer.parseInt(info[125]);
            this._weightRank = Integer.parseInt(info[126]);
            this._moodRank = Integer.parseInt(info[127]);
            this._checksum = info[128];
            this._gameModified = Boolean.parseBoolean(info[129]);
            this._meatEaten = Integer.parseInt(info[130]);
            this._vegEaten = Integer.parseInt(info[131]);
            this._fruitEaten = Integer.parseInt(info[132]);
            this._fishEaten = Integer.parseInt(info[133]);
            this._junkEaten = Integer.parseInt(info[134]);
            this._medEaten = Integer.parseInt(info[135]);
            try {
                this._battleImmunity = Integer.parseInt(info[136]);
            }
            catch (NumberFormatException numberFormatException) {
                // empty catch block
            }
            try {
                this._napCycle = Integer.parseInt(info[137]);
            }
            catch (NumberFormatException numberFormatException) {
                // empty catch block
            }
            try {
                this._obedienceChangeLapse = Byte.parseByte(info[138]);
            }
            catch (NumberFormatException numberFormatException) {
                // empty catch block
            }
            this._settings.setFocus(Boolean.parseBoolean(info[142]));
            this._postponeDie = Boolean.parseBoolean(info[143]);
            this._postponeEvolve = Boolean.parseBoolean(info[144]);
            this._napEnergyInc = Byte.parseByte(info[145]);
            this._saveTime = Long.parseLong(info[146]);
            this._moodRecord[0] = Integer.parseInt(info[148]);
            this._moodRecord[1] = Integer.parseInt(info[149]);
            this._moodRecord[2] = Integer.parseInt(info[150]);
            this._moodRecord[3] = Integer.parseInt(info[151]);
            this._protein = Byte.parseByte(info[153]);
            this._mineral = Byte.parseByte(info[154]);
            this._vitamin = Byte.parseByte(info[155]);
            this._clock.setMinuteBeforeChange(Integer.parseInt(info[156]));
            this._clock.setTimeChanged(Integer.parseInt(info[157]));
            this._clock.setAlarmMinutes(Integer.parseInt(info[158]));
            this._autoCare = Boolean.parseBoolean(info[159]);
            this._tourneyAlarm = Integer.parseInt(info[160]);
            this._minToDecayHunger = Integer.parseInt(info[162]);
            this._xAntibodyState = Enum.XAntibodyState.valueOf(info[163]);
            this._xAntibodyCount = Integer.parseInt(info[164]);
            this._fatigueLength = Byte.parseByte(info[165]);
            this._strengthDecayLapse = Byte.parseByte(info[166]);
            this._minToDecayStrength = Integer.parseInt(info[167]);
            this._foodRanks.getRank(Enum.Food.Med).setRank(Integer.parseInt(info[168]));
            this._foodRanks.getRank(Enum.Food.Junk).setRank(Integer.parseInt(info[169]));
            this._foodRanks.getRank(Enum.Food.Grain).setRank(Integer.parseInt(info[170]));
            this._foodRanks.getRank(Enum.Food.Dairy).setRank(Integer.parseInt(info[171]));
            this._foodRanks.getRank(Enum.Food.None).setRank(Integer.parseInt(info[172]));
            this._timeRanks.getRank(Enum.Time.None).setRank(Integer.parseInt(info[173]));
            this._attributeRanks.getRank(Enum.Attribute.None).setRank(Integer.parseInt(info[174]));
            this._sleepMinutes = Integer.parseInt(info[175]);
            this._dailyMoodRecord[0] = Integer.parseInt(info[176]);
            this._dailyMoodRecord[1] = Integer.parseInt(info[177]);
            this._dailyMoodRecord[2] = Integer.parseInt(info[178]);
            this._dailyMoodRecord[3] = Integer.parseInt(info[179]);
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
            e.printStackTrace();
        }
        this._clock.setSeconds(_seconds, true, this);
        this._clock.setMinutes(_minutes, this);
        this._clock.setHours(_hours, this);
        this.loadSpeciesData();
    }

    public void loadSpeciesData() {
        this.loadSpeciesData(this._evolution.getDigimon(this._index));
    }

    public void loadSpeciesData(EvolutionInfo digimon) {
        byte rankAttribute;
        byte rankTime;
        byte rankFood;
        this._index = digimon.getIndex();
        this._growthStage = digimon.getNewStage();
        this._stomachCapacity = digimon.getStomachCapacity();
        this._attribute = digimon.getNewAttribute();
        this._field = digimon.getNewField();
        this._element = digimon.getNewElement();
        this._idealTemp[0] = digimon.getIdealTemp()[0];
        this._idealTemp[1] = digimon.getIdealTemp()[1];
        this._spriteNum = digimon.getNewSpriteNum();
        this._spriteSet = digimon.getNewSpriteSet();
        this._baseWeight = digimon.getNewWeight();
        switch (digimon.getNewStage()) {
            case Fresh: {
                rankFood = (byte)(Config._rankChangeFood + Config._rankChangeStage1Inc);
                rankTime = (byte)(Config._rankChangeTime + Config._rankChangeStage1Inc);
                rankAttribute = (byte)(Config._rankChangeAttribute + Config._rankChangeStage1Inc);
                break;
            }
            case InTraining: {
                rankFood = (byte)(Config._rankChangeFood + Config._rankChangeStage2Inc);
                rankTime = (byte)(Config._rankChangeTime + Config._rankChangeStage2Inc);
                rankAttribute = (byte)(Config._rankChangeAttribute + Config._rankChangeStage2Inc);
                break;
            }
            case Rookie: {
                rankFood = (byte)(Config._rankChangeFood + Config._rankChangeStage3Inc);
                rankTime = (byte)(Config._rankChangeTime + Config._rankChangeStage3Inc);
                rankAttribute = (byte)(Config._rankChangeAttribute + Config._rankChangeStage3Inc);
                break;
            }
            default: {
                rankFood = Config._rankChangeFood;
                rankTime = Config._rankChangeTime;
                rankAttribute = Config._rankChangeAttribute;
            }
        }
        this._foodRanks.setRankChange(rankFood);
        this._timeRanks.setRankChange(rankTime);
        this._attributeRanks.setRankChange(rankAttribute);
        this._foodRanks.setPreference(digimon.getFoodPreference());
        this._foodRanks.setAversion(digimon.getFoodAversion());
        this._foodRanks.setIntolerant(digimon.getFoodIntolerance());
        if (this._foodRanks.getIntolerant().contains((Object)this._foodRanks.getFavorite())) {
            this._foodRanks.setFavorite(this._foodRanks.getPreference());
        }
        if (this._foodRanks.getIntolerant().contains((Object)this._foodRanks.getDisliked())) {
            this._foodRanks.setDisliked(this._foodRanks.getAversion());
        }
        for (Enum.Food f : this._foodRanks.getIntolerant()) {
            this._foodRanks.getRank(f).setRank(Config._rankMinimum);
        }
        this._timeRanks.setPreference(digimon.getTimePreference());
        this._timeRanks.setAversion(digimon.getTimeAversion());
        this._attributeRanks.setPreference(digimon.getAttributePreference());
        this._attributeRanks.setAversion(digimon.getAttributeAversion());
        this._maxEnergy = digimon.getMaxEnergy();
        this._exerciseLimit = digimon.getMaxStrength();
        if (this._energy > this._maxEnergy) {
            this._energy = this._maxEnergy;
        }
        if (this._exercise > this._exerciseLimit) {
            this._exercise = this._exerciseLimit;
        }
        this._energyGain = digimon.getEnergyGain();
        this._napEnergyGain = digimon.getNapEnergyGain();
        this._sleepMinutesToEnergyGain = digimon.getSleepMinutesToEnergyGain();
        this._hungerDecayCoefficient = digimon.getHungerDecayCoefficient();
        this._strengthDecayCoefficient = digimon.getStrengthDecayCoefficient();
        this._bmLapseInc = digimon.getBMLapseInc();
        this._sleepLapseInc = digimon.getSleepLapseInc();
        this._awakeLapseInc = digimon.getAwakeLapseInc();
        this._bmMax = digimon.getBMMax();
        this._personality = this.checkPersonality();
        this._poopSickBoundMultiplier = digimon.getPoopSickBoundMultiplier();
        this._filthLapseMoodChange = digimon.getFilthLapseMoodChange();
    }

    private void readEvolutionHistory(String[] info) {
        block7: {
            try {
                int evol = 0;
                int i = 0;
                while (evol < info.length) {
                    if (info[i].contains("j")) {
                        String[] s = info[i].split("j");
                        int[] d = new int[]{Integer.parseInt(s[0]), s.length > 1 ? Integer.parseInt(s[1]) : -1};
                        if (d[0] >= 0) {
                            this._evolHistory.add(d);
                        }
                    } else {
                        int d = Integer.parseInt(info[i]);
                        if (d > -1) {
                            this._evolHistory.add(new int[]{d, -1});
                        }
                    }
                    ++evol;
                    ++i;
                }
            }
            catch (NumberFormatException e) {
                if (this._index <= 0) break block7;
                this._evolHistory.add(new int[]{this._index, -1});
            }
        }
    }

    private void readMap(String[] info) {
        try {
            this._world.setEnergyDec(Integer.parseInt(info[0]));
            this._world.setStepInc(Integer.parseInt(info[1]));
            int i = 2;
            for (int num = 1; num < this._world.getMaps().size(); ++num) {
                MapLevel map = this._world.getMaps().get(num);
                map.setIsComplete(Boolean.parseBoolean(info[i]));
                map.setIsCurrent(Boolean.parseBoolean(info[++i]));
                ++i;
                for (Zone zone : map.getZones()) {
                    if (zone == null) continue;
                    zone.setCurrentLocation(Integer.parseInt(info[i]));
                    zone.setIsComplete(Boolean.parseBoolean(info[++i]));
                    zone.setIsCurrent(Boolean.parseBoolean(info[++i]));
                    zone.setIsUnlocked(Boolean.parseBoolean(info[++i]));
                    ++i;
                }
                boolean b = Boolean.parseBoolean(info[i]);
                if (!map.getIsUnlocked()) {
                    map.setIsUnlocked(b);
                }
                ++i;
            }
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
            e.printStackTrace();
        }
    }

    private void readTrophies(String[] info) {
        try {
            if (info.length > 0 && !info[0].isEmpty()) {
                for (String i : info) {
                    String[] sub = i.split(";");
                    Trophy t = this._tournament.getTrophy(Integer.parseInt(sub[0]));
                    t.setEarned(true);
                    if (sub.length > 1 && !Utility.isBlank(sub[1])) {
                        t.setSeasonBeat(Boolean.parseBoolean(sub[1]));
                        continue;
                    }
                    t.setSeasonBeat(true);
                }
            }
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
        }
    }

    private void readDailyTrophies(String[] info) {
        try {
            for (String i : info) {
                this._dailyTrophies.add(Integer.parseInt(i));
            }
        }
        catch (NumberFormatException numberFormatException) {
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
        }
    }

    private void readTrophySchedule(String[] info) {
        try {
            for (int i = 0; i < info.length; ++i) {
                this._trophySchedule[i] = Integer.parseInt(info[i]);
            }
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
            this.setTrophySchedule();
        }
    }

    public int getTrophyIndexInSchedule(int id) {
        int index = -1;
        for (int i = 0; i < this._trophySchedule.length; ++i) {
            if (this._trophySchedule[i] != id) continue;
            index = i;
            break;
        }
        return index;
    }

    private void readFoods(String[] info) {
        try {
            block2: for (String s : info) {
                String[] item = s.split("q");
                String id = item[0];
                String uantity = "";
                String unlocked = "";
                if (item[1].contains("su")) {
                    item = item[1].split("su");
                    uantity = item[0];
                    unlocked = item[1];
                } else {
                    uantity = item[1];
                }
                for (FoodType food : this._foodTypes) {
                    if (food.getID() != Integer.parseInt(id)) continue;
                    food.setCurrentUses(Integer.parseInt(uantity));
                    if (!Boolean.parseBoolean(unlocked)) continue block2;
                    food.setShopUnlocked(Boolean.parseBoolean(unlocked));
                    continue block2;
                }
            }
            for (int i = 0; i < 6; ++i) {
                if (this._foodTypes.get((int)i)._canDecUses) continue;
                this._foodTypes.get(i).setCurrentUses(this._foodTypes.get(i).getStartingUses());
            }
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
            System.out.println(e.getMessage());
        }
    }

    private void readItems(String[] info) {
        try {
            block2: for (String s : info) {
                String[] itemq = s.split("q");
                String[] item = itemq[0].split("o");
                String id = item[0];
                String unlocked = item[1];
                String uses = itemq[1];
                for (Item i : this._items) {
                    if (i.getID() != Integer.parseInt(id)) continue;
                    i.setCurrentUses(Integer.parseInt(uses));
                    boolean u = Boolean.parseBoolean(unlocked);
                    if (i.getShopUnlocked() || !u) continue block2;
                    i.setShopUnlocked(u);
                    continue block2;
                }
            }
            if (!this._items.get((int)80)._canDecUses) {
                this._items.get(80).setCurrentUses(this._items.get(80).getStartingUses());
            }
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
            System.out.println(e.getMessage());
        }
    }

    private void readHabitatRecord(String[] info) {
        try {
            for (int i = 0; i < info.length; ++i) {
                this._habitatRecord[i] = Integer.parseInt(info[i]);
            }
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
            e.printStackTrace();
        }
    }

    private void readTempRecord(String[] info) {
        try {
            if (info.length > 2) {
                int total = 0;
                for (String s : info) {
                    total += Integer.parseInt(s);
                }
                this._tempRecord[0] = info.length;
                this._tempRecord[1] = total;
            } else {
                this._tempRecord[0] = Integer.parseInt(info[0]);
                this._tempRecord[1] = Integer.parseInt(info[1]);
            }
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
            e.printStackTrace();
        }
    }

    private void readObedienceRecord(String[] info) {
        try {
            if (info.length > 2) {
                int total = 0;
                for (String s : info) {
                    total += Integer.parseInt(s);
                }
                this._obedienceRecord[0] = info.length;
                this._obedienceRecord[1] = total;
            } else {
                this._obedienceRecord[0] = Integer.parseInt(info[0]);
                this._obedienceRecord[1] = Integer.parseInt(info[1]);
            }
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
            e.printStackTrace();
        }
    }

    private void readCooldown(String[] info) {
        try {
            ArrayList<Enemy> enemies = this._world.getEnemies();
            for (String s : info) {
                if (s.isEmpty()) continue;
                String[] e = s.split(":");
                enemies.get(Integer.parseInt(e[0])).setCooldown(Integer.parseInt(e[1]));
            }
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
            e.printStackTrace();
        }
    }

    private void readHabitats(String[] info) {
        try {
            int i = 0;
            for (String s : info) {
                this._habitats.get(i).setUnlocked(Boolean.parseBoolean(s));
                ++i;
            }
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
            e.printStackTrace();
        }
    }

    private Affinity buildAffinity() {
        String line;
        BufferedReader reader;
        InputStream in;
        Affinity aff = new Affinity();
        try {
            in = Utility.getInputStream(this.getModFolder(), this.MODEL_FOLDER, "fieldAffinity.csv");
            try {
                reader = new BufferedReader(new InputStreamReader(in));
                try {
                    line = reader.readLine();
                    while ((line = reader.readLine()) != null) {
                        aff.readFieldInfo(line.split(","));
                    }
                }
                finally {
                    reader.close();
                }
            }
            finally {
                if (in != null) {
                    in.close();
                }
            }
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
            e.printStackTrace();
        }
        try {
            in = Utility.getInputStream(this.getModFolder(), this.MODEL_FOLDER, "elementAffinity.csv");
            try {
                reader = new BufferedReader(new InputStreamReader(in));
                try {
                    line = reader.readLine();
                    while ((line = reader.readLine()) != null) {
                        aff.readElementInfo(line.split(","));
                    }
                }
                finally {
                    reader.close();
                }
            }
            finally {
                if (in != null) {
                    in.close();
                }
            }
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
            e.printStackTrace();
        }
        try {
            in = Utility.getInputStream(this.getModFolder(), this.MODEL_FOLDER, "attributeJogress.csv");
            try {
                reader = new BufferedReader(new InputStreamReader(in));
                try {
                    line = reader.readLine();
                    while ((line = reader.readLine()) != null) {
                        aff.readAttributeInfo(line.split(","));
                    }
                }
                finally {
                    reader.close();
                }
            }
            finally {
                if (in != null) {
                    in.close();
                }
            }
        }
        catch (Exception e) {
            CrashEntry.generateEntry(e);
            e.printStackTrace();
        }
        return aff;
    }

    private ArrayList<CareEffect> buildLifeEffects() {
        ArrayList<CareEffect> careEffects = new ArrayList<CareEffect>();
        try (InputStream in = Utility.getInputStream(this.getModFolder(), this.MODEL_FOLDER, "careEffect.csv");
             BufferedReader reader = new BufferedReader(new InputStreamReader(in, "utf-8"));){
            String line = reader.readLine();
            while ((line = reader.readLine()) != null) {
                careEffects.add(new CareEffect(line.split(",")));
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
        return careEffects;
    }

    private ArrayList<Habitat> buildHabitats() {
        ArrayList<Habitat> habitats = new ArrayList<Habitat>();
        try (InputStream in = Utility.getInputStream(this.getModFolder(), this.MODEL_FOLDER, "habitats.csv");
             BufferedReader reader = new BufferedReader(new InputStreamReader(in, "utf-8"));){
            String line = reader.readLine();
            while ((line = reader.readLine()) != null) {
                habitats.add(new Habitat(line.split(",")));
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
        return habitats;
    }

    private ArrayList<FoodType> buildFoodTypes() {
        ArrayList<FoodType> foods = new ArrayList<FoodType>();
        try (InputStream in = Utility.getInputStream(this.getModFolder(), this.MODEL_FOLDER, "foods.csv");
             BufferedReader reader = new BufferedReader(new InputStreamReader(in, "utf-8"));){
            String line = reader.readLine();
            while ((line = reader.readLine()) != null) {
                foods.add(new FoodType(line.split(",")));
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
        return foods;
    }

    private ArrayList<Item> buildItems() {
        ArrayList<Item> items = new ArrayList<Item>();
        try (InputStream in = Utility.getInputStream(this.getModFolder(), this.MODEL_FOLDER, "items.csv");
             BufferedReader reader = new BufferedReader(new InputStreamReader(in, "utf-8"));){
            String line = reader.readLine();
            while ((line = reader.readLine()) != null) {
                Item item = new Item(line.split(","));
                if (item.getID() < 0) continue;
                items.add(item);
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
        return items;
    }

    public void loadTree() {
        String path = "files" + File.separator + "saves" + File.separator + "Shared" + File.separator;
        File f = new File(path + "tree.txt");
        if (!f.exists()) {
            f = new File(path + "tree.sav");
        }
        if (f.exists()) {
            try (FileReader in = new FileReader(f);
                 BufferedReader reader = new BufferedReader(in);){
                ArrayList<EvolutionInfo> digimon = new ArrayList<EvolutionInfo>();
                for (EvolutionInfo e : this._evolution.getEvolDigimon()) {
                    if (e.getIsNatural()) continue;
                    digimon.add(e);
                }
                String[] unlocked = reader.readLine().split(",");
                for (int i = 0; i < unlocked.length; ++i) {
                    if (((EvolutionInfo)digimon.get(i)).getUnlocked()) continue;
                    ((EvolutionInfo)digimon.get(i)).setUnlocked(Boolean.parseBoolean(unlocked[i]));
                }
                this._evolution.checkNaturalUnlocked();
            }
            catch (Exception e) {
                CrashEntry.generateEntry(e);
                e.printStackTrace();
            }
            f = new File(path + "tree.sav");
            if (f.exists()) {
                f.delete();
            }
        }
    }

    private void timeSkip() {
        long nanoseconds = 1000000000L;
        long newNanosecond = System.nanoTime();
        long lapsedNano = newNanosecond - this._saveTime;
        long lapsedSeconds = lapsedNano / nanoseconds;
        long nanoRemainder = lapsedNano % nanoseconds;
        this._clock.setNanoRemainder(this._clock.getNanoRemainder() + nanoRemainder, true, this);
        this.processSkippedSeconds(lapsedSeconds);
        lapsedNano = System.nanoTime() - newNanosecond;
        lapsedSeconds = lapsedNano / nanoseconds;
        nanoRemainder = lapsedNano % nanoseconds;
        this._clock.setNanoRemainder(this._clock.getNanoRemainder() + nanoRemainder, true, this);
        this.processSkippedSeconds(lapsedSeconds);
        this._animQueue.clear();
        this._currentState = Enum.State.Idling;
    }

    private void processSkippedSeconds(long lapsedSeconds) {
        long fullyRecoveredSec = -1L;
        for (long i = 0L; i < lapsedSeconds; ++i) {
            MinLapsePacket f = this._clock.setSeconds((byte)(this._clock.getSeconds() + 1), true, this);
            if (f != null) {
                if (f.getFood() != null) {
                    this.feed(f.getFood(), false, Enum.State.Idling);
                }
                if (f.isCleaned()) {
                    this.clearFilth();
                }
                if (f.isLightSwitch()) {
                    this.setLights(false);
                }
            }
            if (fullyRecoveredSec == -1L && this.isFullyRecovered()) {
                fullyRecoveredSec = i;
            }
            this.checkTournamentTimeOut(i, fullyRecoveredSec);
            this.poop(false);
            this.calcEvol();
            this.checkDeath();
            if (this._alive || lapsedSeconds <= 86400L) continue;
            this.calcNewTime(lapsedSeconds - i + 1L);
            break;
        }
    }

    private void checkTournamentTimeOut(long lapsedSeconds, long recoveredSec) {
        if (this._tournament.getActive() && this.isFullyRecovered() && lapsedSeconds >= (long)Config._battleWait + recoveredSec) {
            this._tournament.setActive(false);
        }
    }

    private void calcEvol() {
        if (this._alive && this._lapsedLife >= this._growthPeriod && this._lapsedLife < this._totalLifespan) {
            this._evolution.evolve(this, -1, -1, false, false, 0);
        }
    }

    private void checkDeath() {
        if (this._lapsedLife >= this._totalLifespan) {
            this._alive = false;
        }
    }

    private void calcNewTime(long seconds) {
        int min = this._clock.getMinutes();
        int hour = this._clock.getHours();
        int sec = this._clock.getSeconds();
        for (long i = 0L; i < seconds; ++i) {
            if (++sec != 60) continue;
            sec = 0;
            if (++min != 60) continue;
            min = 0;
            if (++hour != 24) continue;
            this.dailyChange();
            hour = 0;
        }
        this._clock.setSeconds((byte)sec, true, this);
        this._clock.setMinutes((byte)min, this);
        this._clock.setHours((byte)hour, this);
    }

    public int compareStage(Enum.Stage s) {
        return this._growthStage.compareTo(s);
    }
}

