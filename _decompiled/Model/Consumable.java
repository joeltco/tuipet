/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Controller.Utility;
import Model.Enum;
import Model.PhysicalState;
import Model.ShopConsumable;
import java.util.ArrayList;

public class Consumable {
    protected int _ID;
    protected int _spriteSet;
    protected int _spriteNum;
    protected String _name;
    protected String _description;
    protected String _details;
    protected boolean _canDecUses;
    protected boolean _canIncUses;
    private boolean _shopUnlocked;
    protected boolean _canUnlock;
    protected int _maxUses;
    protected int _startingUses;
    protected int _currentUses;
    protected int _usesPerConsumable;
    protected byte _hunger;
    protected byte _strength;
    protected double _energy;
    protected byte _obedience;
    protected byte _enthusiasm;
    protected int _mood;
    protected byte _calories;
    protected byte _weight;
    protected byte _bmGauge;
    protected int _seconds;
    protected int _vaccine;
    protected int _data;
    protected int _virus;
    protected byte _health;
    protected int _sleepLapse;
    protected boolean _recovered;
    protected boolean _cured;
    protected boolean _healed;
    protected boolean _fatigued;
    protected boolean _depressed;
    protected boolean _sleep;
    protected Enum.Food _favFood;
    protected Enum.Time _favTime;
    protected Enum.Personality _newPersonality;
    protected Enum.Attribute _favAttribute;
    protected byte _mistake;
    protected byte _mistakeDay;
    protected byte _temp;
    protected int _giftChance;
    protected byte _gluttonChange;
    protected byte _restlessChange;
    protected byte _dispositionChange;
    protected byte _disposition;
    protected byte _glutton;
    protected byte _restless;
    protected byte _cureLapseChange;
    protected byte _healLapseChange;
    protected byte _fatigueLapseChange;
    protected boolean _showInInventory;
    protected ShopConsumable _homeShop;
    protected int _evolProbChange;
    protected byte _maxHoursBeforeSleep;
    protected int _effectID;
    protected boolean _disturb;
    protected boolean _listPriority;
    protected boolean _changeToPrefTemp;
    protected boolean _forceUse;
    protected boolean _forceUseWhenAsleep;
    protected ArrayList<Integer> _unlockedFood = new ArrayList();
    protected ArrayList<Integer> _unlockedItem = new ArrayList();

    public int getID() {
        return this._ID;
    }

    public int getSpriteSet() {
        return this._spriteSet;
    }

    public int getMaxUses() {
        return this._maxUses;
    }

    public boolean getCanIncUses() {
        return this._canIncUses;
    }

    public boolean getCanDecUses() {
        return this._canDecUses;
    }

    public int getStartingUses() {
        return this._startingUses;
    }

    public int getCurrentUses() {
        return this._currentUses;
    }

    public int getUsesPerConsumable() {
        return this._usesPerConsumable;
    }

    public int getSpriteNum() {
        return this._spriteNum;
    }

    public String getName() {
        return this._name;
    }

    public String getDescription() {
        return this._description;
    }

    public String getDetails() {
        return this._details;
    }

    public boolean getShopUnlocked() {
        return this._shopUnlocked;
    }

    public void setShopUnlocked(boolean b) {
        if (this._canUnlock) {
            this._shopUnlocked = b;
        }
    }

    public byte getHunger() {
        return this._hunger;
    }

    public byte getStrength() {
        return this._strength;
    }

    public double getEnergy() {
        return this._energy;
    }

    public byte getObedience() {
        return this._obedience;
    }

    public byte getEnthusiasm() {
        return this._enthusiasm;
    }

    public int getMood() {
        return this._mood;
    }

    public byte getCalories() {
        return this._calories;
    }

    public byte getWeight() {
        return this._weight;
    }

    public byte getBMGauge() {
        return this._bmGauge;
    }

    public int getSeconds() {
        return this._seconds;
    }

    public int getVaccine() {
        return this._vaccine;
    }

    public int getData() {
        return this._data;
    }

    public int getVirus() {
        return this._virus;
    }

    public byte getHealth() {
        return this._health;
    }

    public int getSleepLapse() {
        return this._sleepLapse;
    }

    public boolean getRecovered() {
        return this._recovered;
    }

    public boolean getCured() {
        return this._cured;
    }

    public boolean getHealed() {
        return this._healed;
    }

    public boolean getFatigued() {
        return this._fatigued;
    }

    public boolean getDepressed() {
        return this._depressed;
    }

    public boolean getSleep() {
        return this._sleep;
    }

    public Enum.Food getFavFood() {
        return this._favFood;
    }

    public Enum.Time getFavTime() {
        return this._favTime;
    }

    public Enum.Personality getNewPersonality() {
        return this._newPersonality;
    }

    public Enum.Attribute getFavAttribute() {
        return this._favAttribute;
    }

    public byte getMistake() {
        return this._mistake;
    }

    public byte getMistakeDay() {
        return this._mistakeDay;
    }

    public byte getTemp() {
        return this._temp;
    }

    public boolean getCanGift() {
        return Utility.randomChance(this._giftChance, 100);
    }

    public boolean getCanUnlock() {
        return this._canUnlock;
    }

    public byte getGluttonChange() {
        return this._gluttonChange;
    }

    public byte getRestlessChange() {
        return this._restlessChange;
    }

    public byte getDispositionChange() {
        return this._dispositionChange;
    }

    public byte getDisposition() {
        return this._disposition;
    }

    public byte getRestless() {
        return this._restless;
    }

    public byte getGlutton() {
        return this._glutton;
    }

    public byte getCureLapseChange() {
        return this._cureLapseChange;
    }

    public byte getHealLapseChange() {
        return this._healLapseChange;
    }

    public byte getFatigueLapseChange() {
        return this._fatigueLapseChange;
    }

    public boolean getShowInInventory() {
        return this._showInInventory;
    }

    public ShopConsumable getHomeShop() {
        return this._homeShop;
    }

    public int getEvolProbChange() {
        return this._evolProbChange;
    }

    public ArrayList<Integer> getUnlockedFood() {
        return this._unlockedFood;
    }

    public ArrayList<Integer> getUnlockedItem() {
        return this._unlockedItem;
    }

    public boolean isForceUse() {
        return this._forceUse;
    }

    public boolean isForceUseWhenAsleep() {
        return this._forceUseWhenAsleep;
    }

    public void setCurrentUses(int q) {
        this._currentUses = q > 0 && q <= this._maxUses ? q : (q <= 0 ? 0 : this._maxUses);
    }

    public void incQuantity(int i) {
        if (this.canIncQuantity(i)) {
            this.setShopUnlocked(true);
            this.setCurrentUses(this._currentUses + (i *= this._usesPerConsumable));
        }
    }

    public void incQuantity() {
        this.incQuantity(1);
    }

    public void decQuantity() {
        this.decQuantity(1);
    }

    public void decQuantity(int q) {
        if (this._canDecUses) {
            this.setCurrentUses(this._currentUses - q);
        }
    }

    protected void unlockConsumable(PhysicalState digimon, Enum.State state) {
        if (this.canIncQuantity()) {
            digimon.setCurrentState(state);
            this.incQuantity();
        }
    }

    public void remove() {
        this._currentUses = 0;
    }

    public boolean canIncQuantity() {
        return this.canIncQuantity(1);
    }

    public boolean canIncQuantity(int uses) {
        return this._canIncUses && this._currentUses + (uses *= this._usesPerConsumable) <= this._maxUses;
    }

    public byte getMaxHoursBeforeSleep() {
        return this._maxHoursBeforeSleep;
    }

    public int getEffectID() {
        return this._effectID;
    }

    public boolean disturb() {
        return this._disturb;
    }

    public boolean isListPriority() {
        return this._listPriority;
    }

    public boolean changeToPrefTemp() {
        return this._changeToPrefTemp;
    }
}

