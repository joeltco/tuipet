/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Controller.IncorrectRequirement;
import Model.Enum;
import Model.Evolution;
import java.util.AbstractMap;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Random;

public class EvolutionInfo {
    private int _index;
    private int _naturalParentID = -1;
    private boolean _isNatural;
    private String _name = "Default";
    private Enum.Stage _newStage;
    private int _newSpriteNum;
    private byte _newSpriteSet;
    private Enum.Attribute _newAttribute;
    private Enum.Field _newField;
    private Enum.Element _newElement;
    private String _vaccineName = "Jab";
    private Enum.AttackEffect _vaccineEffect = Enum.AttackEffect.None;
    private ArrayList<Enum.AttackCondition> _vaccineConditions = new ArrayList();
    private String _dataName = "Punch";
    private Enum.AttackEffect _dataEffect = Enum.AttackEffect.None;
    private ArrayList<Enum.AttackCondition> _dataConditions = new ArrayList();
    private String _virusName = "Swipe";
    private Enum.AttackEffect _virusEffect = Enum.AttackEffect.None;
    private ArrayList<Enum.AttackCondition> _virusConditions = new ArrayList();
    private ArrayList<EvolutionInfo> _preEvolutions;
    private ArrayList<EvolutionInfo> _evolutions;
    private double _priority;
    private Enum.SpecialEvolution _specialEvol;
    private Map<Enum.Condition, Double>[] _vaccinePower;
    private Map<Enum.Condition, Double>[] _dataPower;
    private Map<Enum.Condition, Double>[] _virusPower;
    private int _vaccineNum;
    private int _dataNum;
    private int _virusNum;
    private Enum.Weight _weight;
    private byte _newWeight;
    private byte _stomachCapacity;
    private Enum.Time _time;
    private Map<Enum.Condition, Integer> _disturb;
    private Map<Enum.Condition, Integer> _overeat;
    private Map<Enum.Condition, Integer> _sick;
    private Map<Enum.Condition, Integer> _injured;
    private Enum.Mood _mood;
    private Map<Enum.Condition, Integer> _obedience;
    private Map<Enum.Condition, Integer> _battles;
    private Map<Enum.Condition, Integer> _wins;
    private Map<Enum.Condition, Integer> _mistakes;
    private byte[] _tempReq;
    private byte[] _idealTemp;
    private Enum.Food _majorFood;
    private Map<Enum.Condition, Integer> _incarnations;
    private int _levelFought;
    private Map<Enum.Condition, Integer> _levelFoughtCondition;
    private Enum.XAntibody _xAntibody;
    private Map<Enum.Condition, Integer> _virusBuster;
    private Map<Enum.Condition, Integer> _metalEmpire;
    private Map<Enum.Condition, Integer> _dragonsRoar;
    private Map<Enum.Condition, Integer> _jungleTrooper;
    private Map<Enum.Condition, Integer> _deepSea;
    private Map<Enum.Condition, Integer> _nightmareSoldier;
    private Map<Enum.Condition, Integer> _windGuardian;
    private Map<Enum.Condition, Integer> _natureSpirit;
    private Map<Enum.Condition, Integer> _darkArea;
    private Map<Enum.Condition, Integer> _none;
    private int _vaccineChange;
    private int _dataChange;
    private int _virusChange;
    private int _lifespanMod;
    private int _growthPeriodMod;
    private int _habitat;
    private int _probBound;
    private int _prob;
    private int _evolItemID = -1;
    private boolean _tournamentAble;
    private boolean _hiddenEvolution;
    private boolean _hiddenPreEvolution;
    private boolean _showEvolutions;
    private boolean _showPreEvolutions;
    private byte _meatRank;
    private byte _fishRank;
    private byte _fruitRank;
    private byte _vegRank;
    private byte _medRank;
    private byte _junkRank;
    private byte _grainRank;
    private byte _dairyRank;
    private byte _morningRank;
    private byte _dayRank;
    private byte _nightRank;
    private byte _vaccineRank;
    private byte _dataRank;
    private byte _virusRank;
    private Enum.Food _foodPreference;
    private Enum.Time _timePreference;
    private Enum.Attribute _attributePreference;
    private Enum.Food _foodAversion;
    private ArrayList<Enum.Food> _foodIntolerance;
    private Enum.Time _timeAversion;
    private Enum.Attribute _attributeAversion;
    private byte _maxEnergy;
    private byte _maxStrength;
    private byte _energyGain;
    private byte _napEnergyGain;
    private ArrayList<Integer> _collapse;
    private double _hungerDecayCoefficient;
    private double _strengthDecayCoefficient;
    private int _sleepLapseInc;
    private int _awakeLapseInc;
    private int _sleepMinutesToEnergyGain;
    private byte _bmLapseInc;
    private byte _bmMax;
    private boolean _isStarter;
    private boolean _isRestarter;
    private int _giveItem = -1;
    private int _evolFoodID = -1;
    private byte _spriteRotations;
    private boolean _listPriority;
    private boolean _canAssist;
    private boolean _resetEvolVars;
    private double _poopSickBoundMultiplier;
    private int _filthLapseMoodChange;
    private boolean _unlocked;

    public int getIndex() {
        return this._index;
    }

    public boolean getIsNatural() {
        return this._isNatural;
    }

    public int getNaturalParent() {
        return this._naturalParentID;
    }

    public String getName() {
        return this._name;
    }

    public Enum.Stage getNewStage() {
        return this._newStage;
    }

    public Enum.Attribute getNewAttribute() {
        return this._newAttribute;
    }

    public Enum.Element getNewElement() {
        return this._newElement;
    }

    public Enum.Field getNewField() {
        return this._newField;
    }

    public String getVaccineName() {
        return this._vaccineName;
    }

    public Enum.AttackEffect getVaccineEffect() {
        return this._vaccineEffect;
    }

    public ArrayList<Enum.AttackCondition> getVaccineConditions() {
        return this._vaccineConditions;
    }

    public String getDataName() {
        return this._dataName;
    }

    public Enum.AttackEffect getDataEffect() {
        return this._dataEffect;
    }

    public ArrayList<Enum.AttackCondition> getDataConditions() {
        return this._dataConditions;
    }

    public String getVirusName() {
        return this._virusName;
    }

    public Enum.AttackEffect getVirusEffect() {
        return this._virusEffect;
    }

    public ArrayList<Enum.AttackCondition> getVirusConditions() {
        return this._virusConditions;
    }

    public int getVaccineNum() {
        return this._vaccineNum;
    }

    public int getDataNum() {
        return this._dataNum;
    }

    public int getVirusNum() {
        return this._virusNum;
    }

    public int getNewSpriteNum() {
        return this._newSpriteNum;
    }

    public byte getNewSpriteSet() {
        return this._newSpriteSet;
    }

    public ArrayList<EvolutionInfo> getPreEvolutions() {
        return this._preEvolutions;
    }

    public ArrayList<EvolutionInfo> getVisiblePreEvolutions(EvolutionInfo prioritizeDuplicate) {
        ArrayList<EvolutionInfo> evols = new ArrayList<EvolutionInfo>();
        if (this._showPreEvolutions) {
            evols = this.getVisibleInfo(this._preEvolutions, true, prioritizeDuplicate);
        }
        return evols;
    }

    private ArrayList<EvolutionInfo> getVisibleInfo(ArrayList<EvolutionInfo> list, boolean isPre, EvolutionInfo prioritizeDuplicate) {
        ArrayList<EvolutionInfo> evols = new ArrayList<EvolutionInfo>();
        int index = -1;
        if (prioritizeDuplicate != null) {
            int p;
            for (int i = 0; i < list.size(); ++i) {
                if (!this.isDuplicate(list.get(i), prioritizeDuplicate)) continue;
                index = i;
                break;
            }
            if (index > -1 && (p = list.indexOf(prioritizeDuplicate)) > -1 && p > index) {
                Collections.swap(list, index, p);
            }
        }
        for (EvolutionInfo e : list) {
            if (!(isPre ? !e.getHiddenPreEvolution() : !e.getHiddenEvolution())) continue;
            if (e.getCollapse() != null && !e.getCollapse().isEmpty()) {
                boolean dup = false;
                for (EvolutionInfo ev : evols) {
                    if (!this.isDuplicate(ev, e)) continue;
                    dup = true;
                    break;
                }
                if (dup) continue;
                evols.add(e);
                continue;
            }
            evols.add(e);
        }
        return evols;
    }

    private boolean isDuplicate(EvolutionInfo current, EvolutionInfo compare) {
        return current.getCollapse() != null && !current.equals(compare) && current.getName().equals(compare.getName()) && current.getCollapse().contains(compare.getIndex());
    }

    public void setPreEvolutions(ArrayList<EvolutionInfo> newPreEvolution) {
        this._preEvolutions = newPreEvolution;
    }

    public ArrayList<EvolutionInfo> getEvolutions() {
        return this._evolutions;
    }

    public ArrayList<EvolutionInfo> getVisibleEvolutions(EvolutionInfo prioritizeDuplicate) {
        ArrayList<EvolutionInfo> evols = new ArrayList<EvolutionInfo>();
        if (this._showEvolutions) {
            evols = this.getVisibleInfo(this._evolutions, false, prioritizeDuplicate);
        }
        return evols;
    }

    public void setParents(ArrayList<EvolutionInfo> newParents) {
        this._evolutions = newParents;
    }

    public Enum.SpecialEvolution getSpecialEvol() {
        return this._specialEvol;
    }

    public double getPriority() {
        return this._priority;
    }

    public void setPriority(double d) {
        this._priority = d;
    }

    public byte getNewWeight() {
        return this._newWeight;
    }

    public int getProbBound() {
        return this._probBound;
    }

    public int getProb() {
        return this._prob;
    }

    public int getEvolItemID() {
        return this._evolItemID;
    }

    public Map<Enum.Condition, Double>[] getRawVaccine() {
        return this._vaccinePower;
    }

    public Map.Entry<Enum.Condition, Double>[] getVaccinePower() {
        Map.Entry<Enum.Condition, Double> entry = new AbstractMap.SimpleEntry<Enum.Condition, Double>(Enum.Condition.None, 0.0);
        Map.Entry[] entries = new Map.Entry[]{entry, entry};
        if (!this._vaccinePower[0].isEmpty()) {
            entries[0] = entry = this._vaccinePower[0].entrySet().iterator().next();
            if (!this._vaccinePower[1].isEmpty()) {
                entries[1] = entry = this._vaccinePower[1].entrySet().iterator().next();
            }
        }
        return entries;
    }

    public Map<Enum.Condition, Double>[] getRawData() {
        return this._dataPower;
    }

    public Map.Entry<Enum.Condition, Double>[] getDataPower() {
        Map.Entry<Enum.Condition, Double> entry = new AbstractMap.SimpleEntry<Enum.Condition, Double>(Enum.Condition.None, 0.0);
        Map.Entry[] entries = new Map.Entry[]{entry, entry};
        if (!this._dataPower[0].isEmpty()) {
            entries[0] = entry = this._dataPower[0].entrySet().iterator().next();
            if (!this._dataPower[1].isEmpty()) {
                entries[1] = entry = this._dataPower[1].entrySet().iterator().next();
            }
        }
        return entries;
    }

    public Map<Enum.Condition, Double>[] getRawVirus() {
        return this._virusPower;
    }

    public Map.Entry<Enum.Condition, Double>[] getVirusPower() {
        Map.Entry<Enum.Condition, Double> entry = new AbstractMap.SimpleEntry<Enum.Condition, Double>(Enum.Condition.None, 0.0);
        Map.Entry[] entries = new Map.Entry[]{entry, entry};
        if (!this._virusPower[0].isEmpty()) {
            entries[0] = entry = this._virusPower[0].entrySet().iterator().next();
            if (!this._virusPower[1].isEmpty()) {
                entries[1] = entry = this._virusPower[1].entrySet().iterator().next();
            }
        }
        return entries;
    }

    public Enum.Weight getWeight() {
        return this._weight;
    }

    public byte getStomachCapacity() {
        return this._stomachCapacity;
    }

    public Enum.Time getTime() {
        return this._time;
    }

    public Map<Enum.Condition, Integer> getRawDisturb() {
        return this._disturb;
    }

    public Map.Entry<Enum.Condition, Integer> getDisturb() {
        Map.Entry<Enum.Condition, Integer> entry = new AbstractMap.SimpleEntry<Enum.Condition, Integer>(Enum.Condition.None, 0);
        if (!this._disturb.isEmpty()) {
            entry = this._disturb.entrySet().iterator().next();
        }
        return entry;
    }

    public Map<Enum.Condition, Integer> getRawOvereat() {
        return this._overeat;
    }

    public Map.Entry<Enum.Condition, Integer> getOvereat() {
        Map.Entry<Enum.Condition, Integer> entry = new AbstractMap.SimpleEntry<Enum.Condition, Integer>(Enum.Condition.None, 0);
        if (!this._overeat.isEmpty()) {
            entry = this._overeat.entrySet().iterator().next();
        }
        return entry;
    }

    public Map<Enum.Condition, Integer> getRawSick() {
        return this._sick;
    }

    public Map.Entry<Enum.Condition, Integer> getSick() {
        Map.Entry<Enum.Condition, Integer> entry = new AbstractMap.SimpleEntry<Enum.Condition, Integer>(Enum.Condition.None, 0);
        if (!this._sick.isEmpty()) {
            entry = this._sick.entrySet().iterator().next();
        }
        return entry;
    }

    public Map<Enum.Condition, Integer> getRawInjured() {
        return this._injured;
    }

    public Map.Entry<Enum.Condition, Integer> getInjured() {
        Map.Entry<Enum.Condition, Integer> entry = new AbstractMap.SimpleEntry<Enum.Condition, Integer>(Enum.Condition.None, 0);
        if (!this._injured.isEmpty()) {
            entry = this._injured.entrySet().iterator().next();
        }
        return entry;
    }

    public Enum.Mood getMood() {
        return this._mood;
    }

    public Map<Enum.Condition, Integer> getRawObedience() {
        return this._obedience;
    }

    public Map.Entry<Enum.Condition, Integer> getObedience() {
        Map.Entry<Enum.Condition, Integer> entry = new AbstractMap.SimpleEntry<Enum.Condition, Integer>(Enum.Condition.None, 0);
        if (!this._obedience.isEmpty()) {
            entry = this._obedience.entrySet().iterator().next();
        }
        return entry;
    }

    public Map<Enum.Condition, Integer> getRawBattles() {
        return this._battles;
    }

    public Map.Entry<Enum.Condition, Integer> getBattles() {
        Map.Entry<Enum.Condition, Integer> entry = new AbstractMap.SimpleEntry<Enum.Condition, Integer>(Enum.Condition.None, 0);
        if (!this._battles.isEmpty()) {
            entry = this._battles.entrySet().iterator().next();
        }
        return entry;
    }

    public Map<Enum.Condition, Integer> getRawWins() {
        return this._wins;
    }

    public Map.Entry<Enum.Condition, Integer> getWins() {
        Map.Entry<Enum.Condition, Integer> entry = new AbstractMap.SimpleEntry<Enum.Condition, Integer>(Enum.Condition.None, 0);
        if (!this._wins.isEmpty()) {
            entry = this._wins.entrySet().iterator().next();
        }
        return entry;
    }

    public Map<Enum.Condition, Integer> getRawMistakes() {
        return this._mistakes;
    }

    public Map.Entry<Enum.Condition, Integer> getMistakes() {
        Map.Entry<Enum.Condition, Integer> entry = new AbstractMap.SimpleEntry<Enum.Condition, Integer>(Enum.Condition.None, 0);
        if (!this._mistakes.isEmpty()) {
            entry = this._mistakes.entrySet().iterator().next();
        }
        return entry;
    }

    public byte[] getTempReq() {
        return this._tempReq;
    }

    public byte[] getIdealTemp() {
        return this._idealTemp;
    }

    public Enum.Food getMajorFood() {
        return this._majorFood;
    }

    public Map<Enum.Condition, Integer> getRawIncarnations() {
        return this._incarnations;
    }

    public Map.Entry<Enum.Condition, Integer> getIncarnations() {
        Map.Entry<Enum.Condition, Integer> entry = new AbstractMap.SimpleEntry<Enum.Condition, Integer>(Enum.Condition.None, 0);
        if (!this._incarnations.isEmpty()) {
            entry = this._incarnations.entrySet().iterator().next();
        }
        return entry;
    }

    public int getLevelFought() {
        return this._levelFought;
    }

    public Map<Enum.Condition, Integer> getRawLevelFoughtCondition() {
        return this._levelFoughtCondition;
    }

    public Map.Entry<Enum.Condition, Integer> getLevelFoughtCondition() {
        Map.Entry<Enum.Condition, Integer> entry = new AbstractMap.SimpleEntry<Enum.Condition, Integer>(Enum.Condition.None, 0);
        if (!this._levelFoughtCondition.isEmpty()) {
            entry = this._levelFoughtCondition.entrySet().iterator().next();
        }
        return entry;
    }

    public Enum.XAntibody getXAntibody() {
        return this._xAntibody;
    }

    public Map<Enum.Condition, Integer> getRawVirusBuster() {
        return this._virusBuster;
    }

    public Map.Entry<Enum.Condition, Integer> getVirusBuster() {
        Map.Entry<Enum.Condition, Integer> entry = new AbstractMap.SimpleEntry<Enum.Condition, Integer>(Enum.Condition.None, 0);
        if (!this._virusBuster.isEmpty()) {
            entry = this._virusBuster.entrySet().iterator().next();
        }
        return entry;
    }

    public Map<Enum.Condition, Integer> getRawMetalEmpire() {
        return this._metalEmpire;
    }

    public Map.Entry<Enum.Condition, Integer> getMetalEmpire() {
        Map.Entry<Enum.Condition, Integer> entry = new AbstractMap.SimpleEntry<Enum.Condition, Integer>(Enum.Condition.None, 0);
        if (!this._metalEmpire.isEmpty()) {
            entry = this._metalEmpire.entrySet().iterator().next();
        }
        return entry;
    }

    public Map<Enum.Condition, Integer> getRawDragonsRoar() {
        return this._dragonsRoar;
    }

    public Map.Entry<Enum.Condition, Integer> getDragonsRoar() {
        Map.Entry<Enum.Condition, Integer> entry = new AbstractMap.SimpleEntry<Enum.Condition, Integer>(Enum.Condition.None, 0);
        if (!this._dragonsRoar.isEmpty()) {
            entry = this._dragonsRoar.entrySet().iterator().next();
        }
        return entry;
    }

    public Map<Enum.Condition, Integer> getRawJungleTrooper() {
        return this._jungleTrooper;
    }

    public Map.Entry<Enum.Condition, Integer> getJungleTrooper() {
        Map.Entry<Enum.Condition, Integer> entry = new AbstractMap.SimpleEntry<Enum.Condition, Integer>(Enum.Condition.None, 0);
        if (!this._jungleTrooper.isEmpty()) {
            entry = this._jungleTrooper.entrySet().iterator().next();
        }
        return entry;
    }

    public Map<Enum.Condition, Integer> getRawDeepSea() {
        return this._deepSea;
    }

    public Map.Entry<Enum.Condition, Integer> getDeepSea() {
        Map.Entry<Enum.Condition, Integer> entry = new AbstractMap.SimpleEntry<Enum.Condition, Integer>(Enum.Condition.None, 0);
        if (!this._deepSea.isEmpty()) {
            entry = this._deepSea.entrySet().iterator().next();
        }
        return entry;
    }

    public Map<Enum.Condition, Integer> getRawNightmareSoldier() {
        return this._nightmareSoldier;
    }

    public Map.Entry<Enum.Condition, Integer> getNightmareSoldier() {
        Map.Entry<Enum.Condition, Integer> entry = new AbstractMap.SimpleEntry<Enum.Condition, Integer>(Enum.Condition.None, 0);
        if (!this._nightmareSoldier.isEmpty()) {
            entry = this._nightmareSoldier.entrySet().iterator().next();
        }
        return entry;
    }

    public Map<Enum.Condition, Integer> getRawWindGuardian() {
        return this._windGuardian;
    }

    public Map.Entry<Enum.Condition, Integer> getWindGuardian() {
        Map.Entry<Enum.Condition, Integer> entry = new AbstractMap.SimpleEntry<Enum.Condition, Integer>(Enum.Condition.None, 0);
        if (!this._windGuardian.isEmpty()) {
            entry = this._windGuardian.entrySet().iterator().next();
        }
        return entry;
    }

    public Map<Enum.Condition, Integer> getRawNatureSpirit() {
        return this._natureSpirit;
    }

    public Map.Entry<Enum.Condition, Integer> getNatureSpirit() {
        Map.Entry<Enum.Condition, Integer> entry = new AbstractMap.SimpleEntry<Enum.Condition, Integer>(Enum.Condition.None, 0);
        if (!this._natureSpirit.isEmpty()) {
            entry = this._natureSpirit.entrySet().iterator().next();
        }
        return entry;
    }

    public Map<Enum.Condition, Integer> getRawDarkArea() {
        return this._darkArea;
    }

    public Map.Entry<Enum.Condition, Integer> getDarkArea() {
        Map.Entry<Enum.Condition, Integer> entry = new AbstractMap.SimpleEntry<Enum.Condition, Integer>(Enum.Condition.None, 0);
        if (!this._darkArea.isEmpty()) {
            entry = this._darkArea.entrySet().iterator().next();
        }
        return entry;
    }

    public Map<Enum.Condition, Integer> getRawNone() {
        return this._none;
    }

    public Map.Entry<Enum.Condition, Integer> getNone() {
        Map.Entry<Enum.Condition, Integer> entry = new AbstractMap.SimpleEntry<Enum.Condition, Integer>(Enum.Condition.None, 0);
        if (!this._none.isEmpty()) {
            entry = this._none.entrySet().iterator().next();
        }
        return entry;
    }

    public boolean getUnlocked() {
        return this._unlocked;
    }

    public void setUnlocked(boolean newUnlocked) {
        this._unlocked = newUnlocked;
    }

    public int getVaccineChange() {
        return this._vaccineChange;
    }

    public int getDataChange() {
        return this._dataChange;
    }

    public int getVirusChange() {
        return this._virusChange;
    }

    public int getLifespanMod() {
        return this._lifespanMod;
    }

    public int getGrowthPeriodMod() {
        return this._growthPeriodMod;
    }

    public int getHabitat() {
        return this._habitat;
    }

    public boolean getTournamentAble() {
        return this._tournamentAble;
    }

    public boolean getHiddenEvolution() {
        return this._hiddenEvolution;
    }

    public boolean getHiddenPreEvolution() {
        return this._hiddenPreEvolution;
    }

    public boolean getShowEvolutions() {
        return this._showEvolutions;
    }

    public boolean getShowPreEvolutions() {
        return this._showPreEvolutions;
    }

    public byte getMeatRank() {
        return this._meatRank;
    }

    public byte getFishRank() {
        return this._fishRank;
    }

    public byte getVegRank() {
        return this._vegRank;
    }

    public byte getFruitRank() {
        return this._fruitRank;
    }

    public byte getMedRank() {
        return this._medRank;
    }

    public byte getJunkRank() {
        return this._junkRank;
    }

    public byte getGrainRank() {
        return this._grainRank;
    }

    public byte getDairyRank() {
        return this._dairyRank;
    }

    public byte getMorningRank() {
        return this._morningRank;
    }

    public byte getDayRank() {
        return this._dayRank;
    }

    public byte getNightRank() {
        return this._nightRank;
    }

    public byte getVaccineRank() {
        return this._vaccineRank;
    }

    public byte getDataRank() {
        return this._dataRank;
    }

    public byte getVirusRank() {
        return this._virusRank;
    }

    public Enum.Food getFoodPreference() {
        return this._foodPreference;
    }

    public Enum.Food getFoodAversion() {
        return this._foodAversion;
    }

    public ArrayList<Enum.Food> getFoodIntolerance() {
        return this._foodIntolerance;
    }

    public Enum.Time getTimePreference() {
        return this._timePreference;
    }

    public Enum.Time getTimeAversion() {
        return this._timeAversion;
    }

    public Enum.Attribute getAttributePreference() {
        return this._attributePreference;
    }

    public Enum.Attribute getAttributeAversion() {
        return this._attributeAversion;
    }

    public byte getMaxEnergy() {
        return this._maxEnergy;
    }

    public byte getMaxStrength() {
        return this._maxStrength;
    }

    public byte getEnergyGain() {
        return this._energyGain;
    }

    public byte getNapEnergyGain() {
        return this._napEnergyGain;
    }

    public ArrayList<Integer> getCollapse() {
        return this._collapse;
    }

    public double getHungerDecayCoefficient() {
        return this._hungerDecayCoefficient;
    }

    public double getStrengthDecayCoefficient() {
        return this._strengthDecayCoefficient;
    }

    public int getSleepLapseInc() {
        return this._sleepLapseInc;
    }

    public int getAwakeLapseInc() {
        return this._awakeLapseInc;
    }

    public int getSleepMinutesToEnergyGain() {
        return this._sleepMinutesToEnergyGain;
    }

    public byte getBMLapseInc() {
        return this._bmLapseInc;
    }

    public byte getBMMax() {
        return this._bmMax;
    }

    public boolean isStarter() {
        return this._isStarter;
    }

    public boolean isRestarter() {
        return this._isRestarter;
    }

    public int getGiveItem() {
        return this._giveItem;
    }

    public int getEvolFoodID() {
        return this._evolFoodID;
    }

    public byte getSpriteRotations() {
        return this._spriteRotations;
    }

    public boolean isListPriority() {
        return this._listPriority;
    }

    public boolean canAssist() {
        return this._canAssist;
    }

    public boolean resetEvolVars() {
        return this._resetEvolVars;
    }

    public double getPoopSickBoundMultiplier() {
        return this._poopSickBoundMultiplier;
    }

    public int getFilthLapseMoodChange() {
        return this._filthLapseMoodChange;
    }

    public EvolutionInfo(int id, int naturalParent, String name, boolean isStarter, Enum.Stage newStage, int newSpriteNum, byte newSpriteSet, Enum.Attribute newAttribute, Enum.Field newField, Enum.Element newElement, String vaccineName, Enum.AttackEffect vaccineEffect, ArrayList<Enum.AttackCondition> vaccineConditions, String dataName, Enum.AttackEffect dataEffect, ArrayList<Enum.AttackCondition> dataConditions, String virusName, Enum.AttackEffect virusEffect, ArrayList<Enum.AttackCondition> virusConditions, ArrayList<EvolutionInfo> preEvolution, ArrayList<EvolutionInfo> evolutions, double difficulty, Enum.SpecialEvolution specialEvol, Map<Enum.Condition, Double>[] vaccinePower, Map<Enum.Condition, Double>[] dataPower, Map<Enum.Condition, Double>[] virusPower, Enum.Weight weight, byte newWeight, byte stomachCapacity, Enum.Time time, Map<Enum.Condition, Integer> disturb, Map<Enum.Condition, Integer> overeat, Map<Enum.Condition, Integer> sick, Map<Enum.Condition, Integer> injured, Enum.Mood mood, Map<Enum.Condition, Integer> obedience, Map<Enum.Condition, Integer> battles, Map<Enum.Condition, Integer> wins, Map<Enum.Condition, Integer> mistakes, byte[] idealTemp, byte[] tempReq, Enum.Food majorFood, Map<Enum.Condition, Integer> incarnations, int levelFought, Map<Enum.Condition, Integer> levelFoughtCondition, Enum.XAntibody xAntibody, Map<Enum.Condition, Integer> virusBuster, Map<Enum.Condition, Integer> metalEmpire, Map<Enum.Condition, Integer> dragonsRoar, Map<Enum.Condition, Integer> jungleTrooper, Map<Enum.Condition, Integer> deepSea, Map<Enum.Condition, Integer> nightmareSoldier, Map<Enum.Condition, Integer> windGuardian, Map<Enum.Condition, Integer> natureSpirit, Map<Enum.Condition, Integer> darkArea, Map<Enum.Condition, Integer> none, int vaccineChange, int dataChange, int virusChange, int lifespanMod, int growthPeriodMod, int evolItem, int prob, int habitat, boolean tournamentAble, boolean hidden, boolean pHidden, boolean showEvolutions, boolean showPreEvolutions, byte meatRank, byte fishRank, byte vegRank, byte fruitRank, byte morningRank, byte dayRank, byte nightRank, byte vaccineRank, byte dataRank, byte virusRank, Enum.Food foodPreference, Enum.Time timePreference, Enum.Attribute attributePreference, byte maxEnergy, byte maxStrength, byte energyGain, byte napEnergyGain, ArrayList<Integer> collapse, double hungerDecayCoefficient, double strengthDecayCoefficient, int sleepLapseInc, int awakeLapseInc, byte bmLapseInc, byte bmMax, int giveItem, int evolFoodID, boolean isRestarter, byte spriteRotations, boolean listPriority, boolean canAssist, byte medRank, byte junkRank, byte grainRank, byte dairyRank, Enum.Food foodAversion, Enum.Time timeAversion, Enum.Attribute attributeAversion, ArrayList<Enum.Food> foodIntolerance, boolean resetEvolVars, int sleepMinutesToEnergyGain, double poopSickBoundMultiplier, int filthLapseMoodChange, boolean unlocked) {
        this._index = id;
        this._naturalParentID = naturalParent;
        this._name = name;
        this._isStarter = isStarter;
        this._newStage = newStage;
        this._newSpriteNum = newSpriteNum;
        this._newSpriteSet = newSpriteSet;
        this._newAttribute = newAttribute;
        this._newField = newField;
        this._newElement = newElement;
        this._vaccineName = vaccineName;
        this._vaccineEffect = vaccineEffect;
        this._vaccineConditions = vaccineConditions;
        this._dataName = dataName;
        this._dataEffect = dataEffect;
        this._dataConditions = dataConditions;
        this._virusName = virusName;
        this._virusEffect = virusEffect;
        this._virusConditions = virusConditions;
        this._preEvolutions = preEvolution;
        this._evolutions = evolutions;
        this._priority = difficulty;
        this._specialEvol = specialEvol;
        this._vaccinePower = vaccinePower;
        this._dataPower = dataPower;
        this._virusPower = virusPower;
        this._weight = weight;
        this._newWeight = newWeight;
        this._stomachCapacity = stomachCapacity;
        this._time = time;
        this._disturb = disturb;
        this._overeat = overeat;
        this._sick = sick;
        this._injured = injured;
        this._mood = mood;
        this._obedience = obedience;
        this._battles = battles;
        this._wins = wins;
        this._mistakes = mistakes;
        this._idealTemp = idealTemp;
        this._tempReq = tempReq;
        this._majorFood = majorFood;
        this._incarnations = incarnations;
        this._levelFought = levelFought;
        this._levelFoughtCondition = levelFoughtCondition;
        this._xAntibody = xAntibody;
        this._virusBuster = virusBuster;
        this._metalEmpire = metalEmpire;
        this._dragonsRoar = dragonsRoar;
        this._jungleTrooper = jungleTrooper;
        this._deepSea = deepSea;
        this._nightmareSoldier = nightmareSoldier;
        this._windGuardian = windGuardian;
        this._natureSpirit = natureSpirit;
        this._darkArea = darkArea;
        this._none = none;
        this._vaccineChange = vaccineChange;
        this._dataChange = dataChange;
        this._virusChange = virusChange;
        this._lifespanMod = lifespanMod;
        this._growthPeriodMod = growthPeriodMod;
        this._evolItemID = evolItem;
        this._prob = prob;
        this._habitat = habitat;
        this._tournamentAble = tournamentAble;
        this._unlocked = unlocked;
        this._hiddenEvolution = hidden;
        this._hiddenPreEvolution = pHidden;
        this._showEvolutions = showEvolutions;
        this._showPreEvolutions = showPreEvolutions;
        this._meatRank = meatRank;
        this._fishRank = fishRank;
        this._vegRank = vegRank;
        this._fruitRank = fruitRank;
        this._morningRank = morningRank;
        this._dayRank = dayRank;
        this._nightRank = nightRank;
        this._vaccineRank = vaccineRank;
        this._dataRank = dataRank;
        this._virusRank = virusRank;
        this._foodPreference = foodPreference;
        this._timePreference = timePreference;
        this._attributePreference = attributePreference;
        this._maxEnergy = maxEnergy;
        this._maxStrength = maxStrength;
        this._energyGain = energyGain;
        this._napEnergyGain = napEnergyGain;
        this._collapse = collapse;
        this._hungerDecayCoefficient = hungerDecayCoefficient;
        this._strengthDecayCoefficient = strengthDecayCoefficient;
        this._sleepLapseInc = sleepLapseInc;
        this._awakeLapseInc = awakeLapseInc;
        this._bmLapseInc = bmLapseInc;
        this._bmMax = bmMax;
        this._evolFoodID = evolFoodID;
        this._giveItem = giveItem;
        this._spriteRotations = spriteRotations;
        this._isRestarter = isRestarter;
        this._listPriority = listPriority;
        this._canAssist = canAssist;
        this._medRank = medRank;
        this._junkRank = junkRank;
        this._grainRank = grainRank;
        this._dairyRank = dairyRank;
        this._foodAversion = foodAversion;
        this._timeAversion = timeAversion;
        this._attributeAversion = attributeAversion;
        this._foodIntolerance = foodIntolerance;
        this._resetEvolVars = resetEvolVars;
        this._sleepMinutesToEnergyGain = sleepMinutesToEnergyGain;
        this._poopSickBoundMultiplier = poopSickBoundMultiplier;
        this._filthLapseMoodChange = filthLapseMoodChange;
    }

    public EvolutionInfo() {
        this._index = -1;
        this._name = "Default";
        this._newStage = Enum.Stage.Fresh;
        this._newSpriteNum = this.getMainSpriteNum(0);
        this._newSpriteSet = 0;
        this._newAttribute = Enum.Attribute.None;
        this._newField = Enum.Field.None;
        this._newElement = Enum.Element.None;
        this._preEvolutions = new ArrayList();
        this._evolutions = new ArrayList();
        this._priority = -1.0;
        this._specialEvol = Enum.SpecialEvolution.None;
        this._vaccinePower = new Map[2];
        this._vaccinePower[0] = new HashMap<Enum.Condition, Double>();
        this._vaccinePower[1] = new HashMap<Enum.Condition, Double>();
        this._dataPower = new Map[2];
        this._dataPower[0] = new HashMap<Enum.Condition, Double>();
        this._dataPower[1] = new HashMap<Enum.Condition, Double>();
        this._virusPower = new Map[2];
        this._virusPower[0] = new HashMap<Enum.Condition, Double>();
        this._virusPower[1] = new HashMap<Enum.Condition, Double>();
        this._weight = Enum.Weight.None;
        this._newWeight = (byte)5;
        this._time = Enum.Time.None;
        this._stomachCapacity = (byte)4;
        this._prob = 100;
        this._disturb = new HashMap<Enum.Condition, Integer>();
        this._overeat = new HashMap<Enum.Condition, Integer>();
        this._sick = new HashMap<Enum.Condition, Integer>();
        this._injured = new HashMap<Enum.Condition, Integer>();
        this._mood = Enum.Mood.None;
        this._obedience = new HashMap<Enum.Condition, Integer>();
        this._battles = new HashMap<Enum.Condition, Integer>();
        this._wins = new HashMap<Enum.Condition, Integer>();
        this._mistakes = new HashMap<Enum.Condition, Integer>();
        this._majorFood = Enum.Food.None;
        this._incarnations = new HashMap<Enum.Condition, Integer>();
        this._levelFought = 0;
        this._levelFoughtCondition = new HashMap<Enum.Condition, Integer>();
        this._virusBuster = new HashMap<Enum.Condition, Integer>();
        this._metalEmpire = new HashMap<Enum.Condition, Integer>();
        this._dragonsRoar = new HashMap<Enum.Condition, Integer>();
        this._jungleTrooper = new HashMap<Enum.Condition, Integer>();
        this._deepSea = new HashMap<Enum.Condition, Integer>();
        this._nightmareSoldier = new HashMap<Enum.Condition, Integer>();
        this._windGuardian = new HashMap<Enum.Condition, Integer>();
        this._natureSpirit = new HashMap<Enum.Condition, Integer>();
        this._darkArea = new HashMap<Enum.Condition, Integer>();
        this._none = new HashMap<Enum.Condition, Integer>();
        this._habitat = -1;
        this._tournamentAble = false;
        this._unlocked = false;
    }

    private int getMainSpriteNum(int column) {
        return column * 11;
    }

    private int getMainEggNum(int column) {
        return 3 * column;
    }

    public void addPreEvolution(EvolutionInfo digimon) {
        this._preEvolutions.add(digimon);
    }

    public void addPreEvolutions(String[] names, ArrayList<EvolutionInfo> allDigimon) {
        for (int i = 0; i < names.length; ++i) {
            for (int inc = 0; inc < allDigimon.size(); ++inc) {
                if (this.preEvolutionContain(names[i]) || !names[i].toUpperCase().equals(allDigimon.get(inc).getName().toUpperCase())) continue;
                this._preEvolutions.add(allDigimon.get(inc));
            }
        }
    }

    public void addEvolution(EvolutionInfo digimon, boolean toEvolutionsPreEvolution) {
        this._evolutions.add(digimon);
        if (toEvolutionsPreEvolution) {
            digimon.addPreEvolution(this);
        }
    }

    public void addEvolutions(Integer[] ids, ArrayList<EvolutionInfo> allDigimon, boolean toEvolutionsPreEvolution) {
        for (int i = 0; i < ids.length; ++i) {
            for (int inc = 0; inc < allDigimon.size(); ++inc) {
                if (allDigimon.get(inc).getIsNatural() || ids[i].intValue() != allDigimon.get(inc).getIndex()) continue;
                this._evolutions.add(allDigimon.get(inc));
                if (!toEvolutionsPreEvolution) continue;
                allDigimon.get(inc).addPreEvolution(this);
            }
        }
    }

    private boolean preEvolutionContain(String name) {
        boolean contains = false;
        for (EvolutionInfo evol : this._preEvolutions) {
            if (evol == null || !evol.getName().equals(name)) continue;
            contains = true;
        }
        return contains;
    }

    private Map.Entry<Enum.Condition, Integer> createMapEntry(Enum.Condition condition, int integer) {
        AbstractMap.SimpleEntry<Enum.Condition, Integer> entry = new AbstractMap.SimpleEntry<Enum.Condition, Integer>(condition, integer);
        return entry;
    }

    public String randomDNARequirements(Evolution e) {
        String s = "";
        int[] dna = new int[Enum.Field.values().length];
        Random r = new Random();
        if (this._newStage != Enum.Stage.Egg && this._newStage != Enum.Stage.Fresh && this._newStage != Enum.Stage.InTraining) {
            int stage = (r.nextInt(7) + 1) * 10;
            int remainder = 90 - stage;
            dna[this._newField.ordinal()] = stage;
            switch (this._newElement) {
                case None: {
                    int n = Enum.Field.None.ordinal();
                    dna[n] = dna[n] + remainder;
                    break;
                }
                case Fire: {
                    int n = Enum.Field.DragonsRoar.ordinal();
                    dna[n] = dna[n] + remainder;
                    break;
                }
                case Light: {
                    int n = Enum.Field.VirusBuster.ordinal();
                    dna[n] = dna[n] + remainder;
                    break;
                }
                case Ice: {
                    int n = Enum.Field.DeepSaver.ordinal();
                    dna[n] = dna[n] + remainder;
                    break;
                }
                case Wind: {
                    int n = Enum.Field.WindGuardian.ordinal();
                    dna[n] = dna[n] + remainder;
                    break;
                }
                case Thunder: {
                    int n = Enum.Field.MetalEmpire.ordinal();
                    dna[n] = dna[n] + remainder;
                    break;
                }
                case Earth: {
                    int n = Enum.Field.NatureSpirit.ordinal();
                    dna[n] = dna[n] + remainder;
                    break;
                }
                case Water: {
                    int n = Enum.Field.DeepSaver.ordinal();
                    dna[n] = dna[n] + remainder;
                    break;
                }
                case Wood: {
                    int n = Enum.Field.JungleTrooper.ordinal();
                    dna[n] = dna[n] + remainder;
                    break;
                }
                case Metal: {
                    int n = Enum.Field.MetalEmpire.ordinal();
                    dna[n] = dna[n] + remainder;
                    break;
                }
                case Dark: {
                    int i = r.nextInt(2);
                    if (i == 0) {
                        int n = Enum.Field.NightmareSoldier.ordinal();
                        dna[n] = dna[n] + remainder;
                        break;
                    }
                    int n = Enum.Field.DarkArea.ordinal();
                    dna[n] = dna[n] + remainder;
                    break;
                }
                default: {
                    throw new AssertionError((Object)this._newElement.name());
                }
            }
            this.checkDNADuplicate(e, r, dna);
            this.checkDNADuplicate(e, r, dna);
            int total = 0;
            for (int i : dna) {
                total += i;
            }
            while (total > 90) {
                int highestValue = 0;
                int fieldIndex = -1;
                for (int i = 0; i < dna.length; ++i) {
                    if (dna[i] <= highestValue) continue;
                    highestValue = dna[i];
                    fieldIndex = i;
                }
                int n = fieldIndex;
                dna[n] = dna[n] - 5;
                total -= 5;
            }
            block29: for (int i = 0; i < dna.length; ++i) {
                if (dna[i] <= 0) continue;
                switch (Enum.Field.values()[i]) {
                    case None: {
                        this._none.clear();
                        this._none.put(Enum.Condition.GreaterThan, dna[i]);
                        continue block29;
                    }
                    case DragonsRoar: {
                        this._dragonsRoar.clear();
                        this._dragonsRoar.put(Enum.Condition.GreaterThan, dna[i]);
                        continue block29;
                    }
                    case DeepSaver: {
                        this._deepSea.clear();
                        this._deepSea.put(Enum.Condition.GreaterThan, dna[i]);
                        continue block29;
                    }
                    case JungleTrooper: {
                        this._jungleTrooper.clear();
                        this._jungleTrooper.put(Enum.Condition.GreaterThan, dna[i]);
                        continue block29;
                    }
                    case MetalEmpire: {
                        this._metalEmpire.clear();
                        this._metalEmpire.put(Enum.Condition.GreaterThan, dna[i]);
                        continue block29;
                    }
                    case NatureSpirit: {
                        this._natureSpirit.clear();
                        this._natureSpirit.put(Enum.Condition.GreaterThan, dna[i]);
                        continue block29;
                    }
                    case WindGuardian: {
                        this._windGuardian.clear();
                        this._windGuardian.put(Enum.Condition.GreaterThan, dna[i]);
                        continue block29;
                    }
                    case NightmareSoldier: {
                        this._nightmareSoldier.clear();
                        this._nightmareSoldier.put(Enum.Condition.GreaterThan, dna[i]);
                        continue block29;
                    }
                    case DarkArea: {
                        this._darkArea.clear();
                        this._darkArea.put(Enum.Condition.GreaterThan, dna[i]);
                        continue block29;
                    }
                    case VirusBuster: {
                        this._virusBuster.clear();
                        this._virusBuster.put(Enum.Condition.GreaterThan, dna[i]);
                        continue block29;
                    }
                    case NA: {
                        continue block29;
                    }
                    default: {
                        throw new AssertionError((Object)Enum.Field.values()[i].name());
                    }
                }
            }
        }
        s = s + (dna[Enum.Field.VirusBuster.ordinal()] > 0 ? "GreaterThan," + dna[Enum.Field.VirusBuster.ordinal()] : "None,0");
        s = s + (dna[Enum.Field.MetalEmpire.ordinal()] > 0 ? ",GreaterThan," + dna[Enum.Field.MetalEmpire.ordinal()] : ",None,0");
        s = s + (dna[Enum.Field.DragonsRoar.ordinal()] > 0 ? ",GreaterThan," + dna[Enum.Field.DragonsRoar.ordinal()] : ",None,0");
        s = s + (dna[Enum.Field.JungleTrooper.ordinal()] > 0 ? ",GreaterThan," + dna[Enum.Field.JungleTrooper.ordinal()] : ",None,0");
        s = s + (dna[Enum.Field.DeepSaver.ordinal()] > 0 ? ",GreaterThan," + dna[Enum.Field.DeepSaver.ordinal()] : ",None,0");
        s = s + (dna[Enum.Field.NightmareSoldier.ordinal()] > 0 ? ",GreaterThan," + dna[Enum.Field.NightmareSoldier.ordinal()] : ",None,0");
        s = s + (dna[Enum.Field.WindGuardian.ordinal()] > 0 ? ",GreaterThan," + dna[Enum.Field.WindGuardian.ordinal()] : ",None,0");
        s = s + (dna[Enum.Field.NatureSpirit.ordinal()] > 0 ? ",GreaterThan," + dna[Enum.Field.NatureSpirit.ordinal()] : ",None,0");
        s = s + (dna[Enum.Field.DarkArea.ordinal()] > 0 ? ",GreaterThan," + dna[Enum.Field.DarkArea.ordinal()] : ",None,0");
        s = s + (dna[Enum.Field.None.ordinal()] > 0 ? ",GreaterThan," + dna[Enum.Field.None.ordinal()] : ",None,0");
        return s;
    }

    private void checkDNADuplicate(Evolution e, Random r, int[] dna) {
        for (EvolutionInfo ev : e.getEvolDigimon()) {
            if (ev._name.equals(this._name) || !(dna[Enum.Field.None.ordinal()] > 0 && ev._none.containsKey((Object)Enum.Condition.GreaterThan) && ev._none.containsValue(dna[Enum.Field.None.ordinal()]) || dna[Enum.Field.DragonsRoar.ordinal()] > 0 && ev._dragonsRoar.containsKey((Object)Enum.Condition.GreaterThan) && ev._dragonsRoar.containsValue(dna[Enum.Field.DragonsRoar.ordinal()]) || dna[Enum.Field.DeepSaver.ordinal()] > 0 && ev._deepSea.containsKey((Object)Enum.Condition.GreaterThan) && ev._deepSea.containsValue(dna[Enum.Field.DeepSaver.ordinal()]) || dna[Enum.Field.JungleTrooper.ordinal()] > 0 && ev._jungleTrooper.containsKey((Object)Enum.Condition.GreaterThan) && ev._jungleTrooper.containsValue(dna[Enum.Field.JungleTrooper.ordinal()]) || dna[Enum.Field.NatureSpirit.ordinal()] > 0 && ev._natureSpirit.containsKey((Object)Enum.Condition.GreaterThan) && ev._natureSpirit.containsValue(dna[Enum.Field.NatureSpirit.ordinal()]) || dna[Enum.Field.WindGuardian.ordinal()] > 0 && ev._windGuardian.containsKey((Object)Enum.Condition.GreaterThan) && ev._windGuardian.containsValue(dna[Enum.Field.WindGuardian.ordinal()]) || dna[Enum.Field.NightmareSoldier.ordinal()] > 0 && ev._nightmareSoldier.containsKey((Object)Enum.Condition.GreaterThan) && ev._nightmareSoldier.containsValue(dna[Enum.Field.NightmareSoldier.ordinal()]) || dna[Enum.Field.DarkArea.ordinal()] > 0 && ev._darkArea.containsKey((Object)Enum.Condition.GreaterThan) && ev._darkArea.containsValue(dna[Enum.Field.DarkArea.ordinal()]) || dna[Enum.Field.VirusBuster.ordinal()] > 0 && ev._virusBuster.containsKey((Object)Enum.Condition.GreaterThan) && ev._virusBuster.containsValue(dna[Enum.Field.VirusBuster.ordinal()])) && (dna[Enum.Field.MetalEmpire.ordinal()] <= 0 || !ev._metalEmpire.containsKey((Object)Enum.Condition.GreaterThan) || !ev._metalEmpire.containsValue(dna[Enum.Field.MetalEmpire.ordinal()]))) continue;
            Enum.Field f = Enum.Field.values()[r.nextInt(Enum.Field.values().length)];
            int n = f.ordinal();
            dna[n] = dna[n] + 5;
            break;
        }
    }

    public String randomizeCSVEffectsConditions(String evol) {
        String finalAttack = "";
        String[] info = evol.split(",");
        Enum.Stage stage = Enum.Stage.valueOf(info[3]);
        if (stage != Enum.Stage.Egg && stage != Enum.Stage.Fresh && stage != Enum.Stage.InTraining) {
            String[] attack = info[48].split(":");
            String[] newAttack = this.randomizeEffectCondition(attack[0]);
            if (Enum.Attribute.valueOf(info[6]) != Enum.Attribute.Vaccine) {
                info[48] = newAttack[0] + ":" + newAttack[1] + ":" + newAttack[2];
            }
            do {
                attack = info[49].split(":");
                newAttack = this.randomizeEffectCondition(attack[0]);
                if (Enum.Attribute.valueOf(info[6]) == Enum.Attribute.Data) continue;
                info[49] = newAttack[0] + ":" + newAttack[1] + ":" + newAttack[2];
            } while (info[48].contains(newAttack[1]) || info[48].contains(newAttack[2]) || info[49].contains("Disable") && info[48].contains("Disable") || newAttack[2].contains("Attack") && info[48].split(":").length > 2 && info[48].split(":")[2].contains("Attack"));
            do {
                attack = info[50].split(":");
                newAttack = this.randomizeEffectCondition(attack[0]);
                if (Enum.Attribute.valueOf(info[6]) == Enum.Attribute.Virus) continue;
                info[50] = newAttack[0] + ":" + newAttack[1] + ":" + newAttack[2];
            } while (info[49].contains(newAttack[1]) || info[49].contains(newAttack[2]) || info[48].contains(newAttack[1]) || info[48].contains(newAttack[2]) || info[50].contains("Disable") && info[49].contains("Disable") || info[50].contains("Disable") && info[48].contains("Disable") || newAttack[2].contains("Attack") && info[48].split(":").length > 2 && info[48].split(":")[2].contains("Attack") || newAttack[2].contains("Attack") && info[49].split(":").length > 2 && info[49].split(":")[2].contains("Attack"));
            for (String s : info) {
                finalAttack = finalAttack + s;
                finalAttack = finalAttack + ",";
            }
        } else {
            finalAttack = evol;
        }
        return finalAttack;
    }

    private String[] randomizeEffectCondition(String name) {
        String[] newAttack = new String[3];
        newAttack[0] = name;
        Random r = new Random();
        do {
            int i = 0;
            while (i >= 15 && i <= 40 || i == 0 || i == 8 || i == 11) {
                i = r.nextInt(Enum.AttackEffect.values().length);
            }
            newAttack[1] = Enum.AttackEffect.values()[i].toString();
            i = 0;
            while (i >= 18 && i <= 37 || i == 0 || i >= 4 && i <= 6) {
                i = r.nextInt(Enum.AttackCondition.values().length - 4);
            }
            newAttack[2] = Enum.AttackCondition.values()[i].toString();
        } while (newAttack[1].equals("First") && newAttack[2].equals("PlayerFirst") || newAttack[1].equals("AttackUp") && newAttack[2].contains("Stronger") || newAttack[1].equals("First") && newAttack[2].equals("PlayerSecond") || newAttack[1].equals("First") && newAttack[2].equals("ForcePlayerSecond") || newAttack[1].equals("Leech") && newAttack[2].equals("SacrificeHealth") || newAttack[1].equals("Absorb") && newAttack[2].equals("SacrificeHealth") || newAttack[1].equals("Counter") && newAttack[2].equals("PlayerSecond") || newAttack[1].equals("Counter") && newAttack[2].equals("ForcePlayerSecond") || newAttack[1].equals("Counter") && newAttack[2].equals("SacrificeAttack") || newAttack[1].equals("Counter") && newAttack[2].equals("SacrificeDefense") || newAttack[1].equals("Leech") && newAttack[2].equals("HigherPlayerHealth") || newAttack[1].contains("Data") && newAttack[2].contains("Data") || newAttack[1].contains("Virus") && newAttack[2].contains("Virus") || newAttack[1].contains("Vaccine") && newAttack[2].contains("Vaccine") || newAttack[1].contains("DefenseUp") && newAttack[2].contains("SacrificeDefense") || newAttack[1].equals("Empty") || newAttack[2].contains("DataStronger") || newAttack[2].contains("DataWeaker") || newAttack[2].contains("VaccineStronger") || newAttack[2].contains("VaccineWeaker") || newAttack[2].contains("VirusStronger") || newAttack[2].contains("VirusWeaker") || newAttack[2].contains("PlayerStronger") || newAttack[2].contains("PlayerWeaker") || newAttack[1].contains("DisableAttack") && newAttack[2].contains("ForcePlayerSecond") || newAttack[1].contains("DisableAttack") && newAttack[2].contains("LowerPlayerHealth") || newAttack[2].contains("HigherPlayerHealth") || newAttack[1].contains("DisableAttack") && newAttack[2].contains("HalfPlayerHealth") || newAttack[2].contains("HalfOppHealth") || newAttack[1].contains("DisableAttack") && newAttack[2].contains("Half") || newAttack[1].contains("DisableAttack") && newAttack[2].contains("PlayerSecond") || newAttack[1].contains("DisableAttack") && newAttack[2].contains("PlayerFirst") || newAttack[1].contains("DisableAttack") && newAttack[2].contains("Lower") || newAttack[1].contains("DisableAttack") && newAttack[2].contains("Higher") || newAttack[1].contains("DisableAttack") && newAttack[2].contains("SacrificeDefense") || newAttack[1].contains("DisableAttack") && newAttack[2].contains("SacrificeAttack") || newAttack[2].contains("PlayerStronger") || newAttack[2].contains("EnemyIs") || newAttack[2].contains("PlayerIs") || newAttack[1].contains("Force") && newAttack[2].contains("Stronger") || newAttack[1].contains("Force") && newAttack[2].contains("Higher") || newAttack[1].contains("Force") && newAttack[2].contains("Lower") || newAttack[1].contains("Force") && newAttack[2].contains("Weaker") || newAttack[1].contains("Force") && newAttack[2].contains("Enemy") || newAttack[1].contains("Force") && !newAttack[2].contains("Attack") || newAttack[1].contains("Force") && newAttack[2].contains("SacrificeAttack") || newAttack[1].contains("Weaken") && newAttack[2].contains("Sacrifice") || newAttack[1].contains("First") && newAttack[2].contains("Enemy") || newAttack[1].contains("Weaken") && !newAttack[2].contains("Attack"));
        return newAttack;
    }

    public EvolutionInfo readInfoString(String evol) {
        try {
            int i;
            String[] info = evol.split(",");
            this._index = Integer.parseInt(info[0]);
            this._naturalParentID = Integer.parseInt(info[1]);
            this._name = info[2];
            this._isStarter = Boolean.parseBoolean(info[3]);
            try {
                this._newStage = Enum.Stage.valueOf(info[4]);
                this._newSpriteNum = Integer.parseInt(info[5]);
                this._newSpriteSet = Byte.parseByte(info[6]);
                this._newAttribute = Enum.Attribute.valueOf(info[7]);
                this._newField = Enum.Field.valueOf(info[8]);
                this._newElement = Enum.Element.valueOf(info[9]);
                String[] temp = info[10].split("t");
                this._tempReq = new byte[]{Byte.parseByte(temp[0]), Byte.parseByte(temp[1])};
                this._priority = Double.parseDouble(info[11]);
                this._specialEvol = Enum.SpecialEvolution.valueOf(info[12]);
                this._vaccinePower[0].put(Enum.Condition.valueOf(info[13]), Double.valueOf(info[14]));
                this._vaccinePower[1].put(Enum.Condition.valueOf(info[15]), Double.valueOf(info[16]));
                this._dataPower[0].put(Enum.Condition.valueOf(info[17]), Double.valueOf(info[18]));
                this._dataPower[1].put(Enum.Condition.valueOf(info[19]), Double.valueOf(info[20]));
                this._virusPower[0].put(Enum.Condition.valueOf(info[21]), Double.valueOf(info[22]));
                this._virusPower[1].put(Enum.Condition.valueOf(info[23]), Double.valueOf(info[24]));
                this._weight = Enum.Weight.valueOf(info[25]);
                this._isRestarter = Boolean.parseBoolean(info[26]);
                this._newWeight = Byte.parseByte(info[27]);
                this._stomachCapacity = Byte.parseByte(info[28]);
                this._time = Enum.Time.valueOf(info[29]);
                this._disturb.put(Enum.Condition.valueOf(info[30]), Integer.parseInt(info[31]));
                this._overeat.put(Enum.Condition.valueOf(info[32]), Integer.parseInt(info[33]));
                this._sick.put(Enum.Condition.valueOf(info[34]), Integer.parseInt(info[35]));
                this._injured.put(Enum.Condition.valueOf(info[36]), Integer.parseInt(info[37]));
                this._habitat = Integer.parseInt(info[38]);
                this._mood = Enum.Mood.valueOf(info[39]);
                this._obedience.put(Enum.Condition.valueOf(info[40]), Integer.parseInt(info[41]));
                this._battles.put(Enum.Condition.valueOf(info[42]), Integer.parseInt(info[43]));
                this._wins.put(Enum.Condition.valueOf(info[44]), Integer.parseInt(info[45]));
                this._mistakes.put(Enum.Condition.valueOf(info[46]), Integer.parseInt(info[47]));
            }
            catch (IllegalArgumentException e) {
                e.printStackTrace();
            }
            String[] prob = info[48].split(";");
            this._prob = Integer.parseInt(prob[0]);
            this._probBound = Integer.parseInt(prob[1]);
            this._unlocked = Boolean.parseBoolean(info[49]);
            String[] nameEffect = info[50].split(":");
            this._vaccineName = nameEffect[0];
            try {
                this._vaccineEffect = Enum.AttackEffect.valueOf(nameEffect[1]);
                for (i = 2; i < nameEffect.length; ++i) {
                    this._vaccineConditions.add(Enum.AttackCondition.valueOf(nameEffect[i]));
                }
            }
            catch (IllegalArgumentException e) {
                this._vaccineEffect = Enum.AttackEffect.None;
                this._vaccineConditions.clear();
                System.out.println(this._name + " - " + this._vaccineName + ": AttackEffect/Condition syntax error");
            }
            nameEffect = info[51].split(":");
            this._dataName = nameEffect[0];
            try {
                this._dataEffect = Enum.AttackEffect.valueOf(nameEffect[1]);
                for (i = 2; i < nameEffect.length; ++i) {
                    this._dataConditions.add(Enum.AttackCondition.valueOf(nameEffect[i]));
                }
            }
            catch (IllegalArgumentException e) {
                this._dataEffect = Enum.AttackEffect.None;
                this._dataConditions.clear();
                System.out.println(this._name + " - " + this._dataName + ": AttackEffect/Condition syntax error");
            }
            nameEffect = info[52].split(":");
            this._virusName = nameEffect[0];
            try {
                this._virusEffect = Enum.AttackEffect.valueOf(nameEffect[1]);
                for (int i2 = 2; i2 < nameEffect.length; ++i2) {
                    this._virusConditions.add(Enum.AttackCondition.valueOf(nameEffect[i2]));
                }
            }
            catch (IllegalArgumentException e) {
                this._virusEffect = Enum.AttackEffect.None;
                this._virusConditions.clear();
                System.out.println(this._name + " - " + this._virusName + ": AttackEffect/Condition syntax error");
            }
            String[] temp = info[53].split("t");
            this._idealTemp = new byte[]{Byte.parseByte(temp[0]), Byte.parseByte(temp[1])};
            String[] attacks = info[54].split(":");
            this._vaccineNum = Integer.parseInt(attacks[0]);
            this._dataNum = Integer.parseInt(attacks[1]);
            this._virusNum = Integer.parseInt(attacks[2]);
            this._majorFood = Enum.Food.valueOf(info[55]);
            this._incarnations.put(Enum.Condition.valueOf(info[56]), Integer.parseInt(info[57]));
            this._levelFought = Integer.parseInt(info[58]);
            this._levelFoughtCondition.put(Enum.Condition.valueOf(info[59]), Integer.parseInt(info[60]));
            this._xAntibody = Enum.XAntibody.valueOf(info[61]);
            this._virusBuster.put(Enum.Condition.valueOf(info[62]), Integer.parseInt(info[63]));
            this._metalEmpire.put(Enum.Condition.valueOf(info[64]), Integer.parseInt(info[65]));
            this._dragonsRoar.put(Enum.Condition.valueOf(info[66]), Integer.parseInt(info[67]));
            this._jungleTrooper.put(Enum.Condition.valueOf(info[68]), Integer.parseInt(info[69]));
            this._deepSea.put(Enum.Condition.valueOf(info[70]), Integer.parseInt(info[71]));
            this._nightmareSoldier.put(Enum.Condition.valueOf(info[72]), Integer.parseInt(info[73]));
            this._windGuardian.put(Enum.Condition.valueOf(info[74]), Integer.parseInt(info[75]));
            this._natureSpirit.put(Enum.Condition.valueOf(info[76]), Integer.parseInt(info[77]));
            this._darkArea.put(Enum.Condition.valueOf(info[78]), Integer.parseInt(info[79]));
            this._none.put(Enum.Condition.valueOf(info[80]), Integer.parseInt(info[81]));
            this.checkDNAAccelLimit();
            this._vaccineChange = Integer.parseInt(info[82]);
            this._dataChange = Integer.parseInt(info[83]);
            this._virusChange = Integer.parseInt(info[84]);
            this._lifespanMod = Integer.parseInt(info[85]);
            this._growthPeriodMod = Integer.parseInt(info[86]);
            this._evolItemID = Integer.parseInt(info[87]);
            this._tournamentAble = Boolean.parseBoolean(info[88]);
            this._hiddenEvolution = Boolean.parseBoolean(info[89]);
            this._hiddenPreEvolution = Boolean.parseBoolean(info[90]);
            this._showEvolutions = Boolean.parseBoolean(info[91]);
            this._showPreEvolutions = Boolean.parseBoolean(info[92]);
            this._meatRank = Byte.parseByte(info[93]);
            this._fishRank = Byte.parseByte(info[94]);
            this._vegRank = Byte.parseByte(info[95]);
            this._fruitRank = Byte.parseByte(info[96]);
            this._morningRank = Byte.parseByte(info[97]);
            this._dayRank = Byte.parseByte(info[98]);
            this._nightRank = Byte.parseByte(info[99]);
            this._vaccineRank = Byte.parseByte(info[100]);
            this._dataRank = Byte.parseByte(info[101]);
            this._virusRank = Byte.parseByte(info[102]);
            this._foodPreference = Enum.Food.valueOf(info[103]);
            this._timePreference = Enum.Time.valueOf(info[104]);
            this._attributePreference = Enum.Attribute.valueOf(info[105]);
            this._maxEnergy = Byte.parseByte(info[106]);
            this._maxStrength = Byte.parseByte(info[107]);
            this._energyGain = Byte.parseByte(info[108]);
            this._napEnergyGain = Byte.parseByte(info[109]);
            String[] c = info[110].split(";");
            ArrayList<Integer> i3 = new ArrayList<Integer>();
            for (String s : c) {
                int id = Integer.parseInt(s);
                if (id <= -1) continue;
                i3.add(id);
            }
            this._collapse = i3;
            this._hungerDecayCoefficient = Double.parseDouble(info[111]);
            this._strengthDecayCoefficient = Double.parseDouble(info[112]);
            this._sleepLapseInc = Integer.parseInt(info[113]);
            this._awakeLapseInc = Integer.parseInt(info[114]);
            this._bmLapseInc = Byte.parseByte(info[115]);
            this._bmMax = Byte.parseByte(info[116]);
            this._giveItem = Integer.parseInt(info[117]);
            this._evolFoodID = Integer.parseInt(info[118]);
            this._spriteRotations = Byte.parseByte(info[119]);
            this._listPriority = Boolean.parseBoolean(info[120]);
            this._canAssist = Boolean.parseBoolean(info[121]);
            this._medRank = Byte.parseByte(info[122]);
            this._junkRank = Byte.parseByte(info[123]);
            this._grainRank = Byte.parseByte(info[124]);
            this._dairyRank = Byte.parseByte(info[125]);
            this._foodAversion = Enum.Food.valueOf(info[126]);
            this._timeAversion = Enum.Time.valueOf(info[127]);
            this._attributeAversion = Enum.Attribute.valueOf(info[128]);
            String[] intol = info[129].split(";");
            this._foodIntolerance = new ArrayList();
            for (String s : intol) {
                Enum.Food f = Enum.Food.valueOf(s);
                if (f == Enum.Food.None) continue;
                this._foodIntolerance.add(f);
            }
            this._resetEvolVars = Boolean.parseBoolean(info[130]);
            this._sleepMinutesToEnergyGain = Integer.parseInt(info[131]);
            this._poopSickBoundMultiplier = Double.parseDouble(info[132]);
            this._filthLapseMoodChange = Integer.parseInt(info[133]);
        }
        catch (ArrayIndexOutOfBoundsException e) {
            System.out.println("ArrayIndexOutOfBounds: Index - " + e.getLocalizedMessage());
            System.out.println(this._name);
        }
        return this;
    }

    private void checkDNAReqQuantity(int i) {
        int q = 0;
        if (this._virusBuster.get((Object)Enum.Condition.GreaterThan) != null) {
            ++q;
        }
        if (this._metalEmpire.get((Object)Enum.Condition.GreaterThan) != null) {
            ++q;
        }
        if (this._dragonsRoar.get((Object)Enum.Condition.GreaterThan) != null) {
            ++q;
        }
        if (this._jungleTrooper.get((Object)Enum.Condition.GreaterThan) != null) {
            ++q;
        }
        if (this._deepSea.get((Object)Enum.Condition.GreaterThan) != null) {
            ++q;
        }
        if (this._nightmareSoldier.get((Object)Enum.Condition.GreaterThan) != null) {
            ++q;
        }
        if (this._windGuardian.get((Object)Enum.Condition.GreaterThan) != null) {
            ++q;
        }
        if (this._natureSpirit.get((Object)Enum.Condition.GreaterThan) != null) {
            ++q;
        }
        if (this._darkArea.get((Object)Enum.Condition.GreaterThan) != null) {
            ++q;
        }
        if (this._none.get((Object)Enum.Condition.GreaterThan) != null) {
            ++q;
        }
        if (q < i) {
            System.out.println(this._name);
        }
    }

    private void checkDNAAccelLimit() throws IncorrectRequirement {
        int total = 0;
        if (this.getVirusBuster().getKey() == Enum.Condition.GreaterThan) {
            total += this.getVirusBuster().getValue() + 1;
        }
        if (this.getDragonsRoar().getKey() == Enum.Condition.GreaterThan) {
            total += this.getDragonsRoar().getValue() + 1;
        }
        if (this.getMetalEmpire().getKey() == Enum.Condition.GreaterThan) {
            total += this.getMetalEmpire().getValue() + 1;
        }
        if (this.getJungleTrooper().getKey() == Enum.Condition.GreaterThan) {
            total += this.getJungleTrooper().getValue() + 1;
        }
        if (this.getDeepSea().getKey() == Enum.Condition.GreaterThan) {
            total += this.getDeepSea().getValue() + 1;
        }
        if (this.getNightmareSoldier().getKey() == Enum.Condition.GreaterThan) {
            total += this.getNightmareSoldier().getValue() + 1;
        }
        if (this.getWindGuardian().getKey() == Enum.Condition.GreaterThan) {
            total += this.getWindGuardian().getValue() + 1;
        }
        if (this.getNatureSpirit().getKey() == Enum.Condition.GreaterThan) {
            total += this.getNatureSpirit().getValue() + 1;
        }
        if (this.getDarkArea().getKey() == Enum.Condition.GreaterThan) {
            total += this.getDarkArea().getValue() + 1;
        }
        if (this.getNone().getKey() == Enum.Condition.GreaterThan) {
            total += this.getNone().getValue() + 1;
        }
        if (total > 100) {
            throw new IncorrectRequirement(this._index + " DNA above 100%");
        }
    }

    public String infoToString() {
        StringBuilder evol = new StringBuilder();
        String delin = ",";
        evol.append(this._naturalParentID);
        evol.append(delin);
        evol.append(this._name);
        evol.append(delin);
        evol.append(this._isStarter);
        evol.append(delin);
        evol.append(this._newStage.toString());
        evol.append(delin);
        evol.append(this._newSpriteNum);
        evol.append(delin);
        evol.append(this._newSpriteSet);
        evol.append(delin);
        evol.append(this._newAttribute.toString());
        evol.append(delin);
        evol.append(this._newField.toString());
        evol.append(delin);
        evol.append("");
        evol.append(delin);
        evol.append(this._priority);
        evol.append(delin);
        evol.append((Object)this._specialEvol);
        evol.append(delin);
        evol.append(this.getVaccinePower()[0].getKey().toString());
        evol.append(delin);
        evol.append(this.getVaccinePower()[0].getValue().toString());
        evol.append(delin);
        evol.append(this.getVaccinePower()[1].getKey().toString());
        evol.append(delin);
        evol.append(this.getVaccinePower()[1].getValue().toString());
        evol.append(delin);
        evol.append(this.getDataPower()[0].getKey().toString());
        evol.append(delin);
        evol.append(this.getDataPower()[0].getValue().toString());
        evol.append(delin);
        evol.append(this.getDataPower()[1].getKey().toString());
        evol.append(delin);
        evol.append(this.getDataPower()[1].getValue().toString());
        evol.append(delin);
        evol.append(this.getVirusPower()[0].getKey().toString());
        evol.append(delin);
        evol.append(this.getVirusPower()[0].getValue().toString());
        evol.append(delin);
        evol.append(this.getVirusPower()[1].getKey().toString());
        evol.append(delin);
        evol.append(this.getVirusPower()[1].getValue().toString());
        evol.append(delin);
        evol.append("");
        evol.append(delin);
        evol.append((Object)this.getWeight());
        evol.append(delin);
        evol.append(this._newWeight);
        evol.append(delin);
        evol.append(this._stomachCapacity);
        evol.append(delin);
        evol.append(this._time.toString());
        evol.append(delin);
        evol.append(this.getDisturb().getKey().toString());
        evol.append(delin);
        evol.append(this.getDisturb().getValue().toString());
        evol.append(delin);
        evol.append(this.getOvereat().getKey().toString());
        evol.append(delin);
        evol.append(this.getOvereat().getValue().toString());
        evol.append(delin);
        evol.append(this.getSick().getKey().toString());
        evol.append(delin);
        evol.append(this.getSick().getValue().toString());
        evol.append(delin);
        evol.append(this.getInjured().getKey().toString());
        evol.append(delin);
        evol.append(this.getInjured().getValue().toString());
        evol.append(delin);
        evol.append("");
        evol.append(delin);
        evol.append(this.getMood().toString());
        evol.append(delin);
        evol.append(this.getObedience().getKey().toString());
        evol.append(delin);
        evol.append(this.getObedience().getValue().toString());
        evol.append(delin);
        evol.append(this.getBattles().getKey().toString());
        evol.append(delin);
        evol.append(this.getBattles().getValue().toString());
        evol.append(delin);
        evol.append(this.getWins().getKey().toString());
        evol.append(delin);
        evol.append(this.getWins().getValue().toString());
        evol.append(delin);
        evol.append(this.getMistakes().getKey().toString());
        evol.append(delin);
        evol.append(this.getMistakes().getValue().toString());
        evol.append(delin);
        evol.append(this._prob);
        evol.append(delin);
        evol.append(this._unlocked);
        evol.append(delin);
        String attackInfo = this._vaccineName + ":" + (this._vaccineEffect.equals("") ? "None" : this._vaccineEffect);
        for (Enum.AttackCondition c : this._vaccineConditions) {
            attackInfo = attackInfo + ":" + (Object)((Object)c);
        }
        return evol.toString();
    }

    public String evolutionsToString() {
        StringBuilder evolutions = new StringBuilder();
        String delin = ",";
        evolutions.append(this._name);
        evolutions.append(delin);
        for (EvolutionInfo evol : this._evolutions) {
            if (evol == null) continue;
            evolutions.append(evol._name);
            evolutions.append(delin);
        }
        return evolutions.toString();
    }

    public void setNatural() {
        this._isNatural = true;
        this._time = Enum.Time.None;
        this._priority = -1.0;
    }
}

