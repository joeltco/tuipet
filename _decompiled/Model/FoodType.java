/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Model.Consumable;
import Model.Enum;
import Model.PhysicalState;
import Model.ShopConsumable;
import java.util.ArrayList;

public class FoodType
extends Consumable {
    private ArrayList<Enum.Food> _type = new ArrayList();
    private byte _protein;
    private byte _vitamin;
    private byte _mineral;

    public ArrayList<Enum.Food> getType() {
        return this._type;
    }

    public byte getProtein() {
        return this._protein;
    }

    public byte getVitamin() {
        return this._vitamin;
    }

    public byte getMineral() {
        return this._mineral;
    }

    public byte getTotalNutrition() {
        return (byte)(this._protein + this._vitamin + this._mineral);
    }

    public FoodType(String[] info) {
        String[] unlock;
        String[] list;
        this._ID = Integer.parseInt(info[0]);
        this._spriteSet = Integer.parseInt(info[1]);
        this._spriteNum = Integer.parseInt(info[2]);
        this._name = info[3];
        this._description = info[4];
        int price = Integer.parseInt(info[5]);
        this._hunger = Byte.parseByte(info[6]);
        this._strength = Byte.parseByte(info[7]);
        this._energy = Double.parseDouble(info[8]);
        this._obedience = Byte.parseByte(info[9]);
        this._enthusiasm = Byte.parseByte(info[10]);
        this._mood = Byte.parseByte(info[11]);
        this._calories = Byte.parseByte(info[12]);
        this._weight = Byte.parseByte(info[13]);
        this._bmGauge = Byte.parseByte(info[14]);
        this._seconds = Integer.parseInt(info[15]);
        this._vaccine = Byte.parseByte(info[16]);
        this._data = Byte.parseByte(info[17]);
        this._virus = Byte.parseByte(info[18]);
        this._health = Byte.parseByte(info[19]);
        this._recovered = Boolean.parseBoolean(info[20]);
        this._cured = Boolean.parseBoolean(info[21]);
        this._healed = Boolean.parseBoolean(info[22]);
        this._fatigued = Boolean.parseBoolean(info[23]);
        this._depressed = Boolean.parseBoolean(info[24]);
        this._favFood = Enum.Food.valueOf(info[25]);
        this._favTime = Enum.Time.valueOf(info[26]);
        this._newPersonality = Enum.Personality.valueOf(info[27]);
        this._favAttribute = Enum.Attribute.valueOf(info[28]);
        this._mistake = Byte.parseByte(info[29]);
        for (String s : list = info[30].split(";")) {
            this._type.add(Enum.Food.valueOf(s));
        }
        this._sleep = Boolean.parseBoolean(info[31]);
        this._sleepLapse = Integer.parseInt(info[32]);
        this._temp = Byte.parseByte(info[33]);
        this._giftChance = Integer.parseInt(info[34]);
        this._canUnlock = Boolean.parseBoolean(info[36]);
        this.setShopUnlocked(Boolean.parseBoolean(info[35]));
        this._dispositionChange = Byte.parseByte(info[37]);
        this._gluttonChange = Byte.parseByte(info[38]);
        this._restlessChange = Byte.parseByte(info[39]);
        this._protein = Byte.parseByte(info[40]);
        this._vitamin = Byte.parseByte(info[41]);
        this._mineral = Byte.parseByte(info[42]);
        this._glutton = Byte.parseByte(info[43]);
        this._restless = Byte.parseByte(info[44]);
        this._disposition = Byte.parseByte(info[45]);
        this._canIncUses = Boolean.parseBoolean(info[46]);
        this._canDecUses = Boolean.parseBoolean(info[47]);
        this._startingUses = Byte.parseByte(info[48]);
        this._showInInventory = Boolean.parseBoolean(info[49]);
        this._maxUses = Integer.parseInt(info[50]);
        String[] s = info[51].split(";");
        byte[] defaultStockChance = new byte[]{Byte.parseByte(s[0]), Byte.parseByte(s[1]), Byte.parseByte(s[2]), Byte.parseByte(s[3])};
        byte defaultMaxStock = Byte.parseByte(info[52]);
        byte defaultMinStock = Byte.parseByte(info[53]);
        String[] ranges = info[54].split(";");
        ArrayList<byte[]> defaultTimeAvailable = new ArrayList<byte[]>();
        for (String r : ranges) {
            String[] time = r.split("t");
            defaultTimeAvailable.add(new byte[]{Byte.parseByte(time[0]), Byte.parseByte(time[1])});
        }
        boolean mustStock = Boolean.parseBoolean(info[55]);
        this._usesPerConsumable = Integer.parseInt(info[56]);
        s = info[57].split(";");
        byte[] defaultSaleChance = new byte[]{Byte.parseByte(s[0]), Byte.parseByte(s[1]), Byte.parseByte(s[2]), Byte.parseByte(s[3])};
        byte defaultSaleFactor = Byte.parseByte(info[58]);
        byte defaultResellFactor = Byte.parseByte(info[59]);
        this._homeShop = new ShopConsumable(this._ID, true, defaultStockChance, defaultMaxStock, defaultMinStock, defaultTimeAvailable, price, mustStock, defaultSaleChance, defaultSaleFactor, defaultResellFactor);
        this._healLapseChange = Byte.parseByte(info[60]);
        this._cureLapseChange = Byte.parseByte(info[61]);
        this._fatigueLapseChange = Byte.parseByte(info[62]);
        this._evolProbChange = Integer.parseInt(info[63]);
        this._maxHoursBeforeSleep = Byte.parseByte(info[64]);
        this._effectID = Integer.parseInt(info[65]);
        this._disturb = Boolean.parseBoolean(info[66]);
        this._listPriority = Boolean.parseBoolean(info[67]);
        this._changeToPrefTemp = Boolean.parseBoolean(info[68]);
        this._mistakeDay = Byte.parseByte(info[69]);
        this._forceUse = Boolean.parseBoolean(info[70]);
        this._forceUseWhenAsleep = Boolean.parseBoolean(info[71]);
        for (String u : unlock = info[72].split(";")) {
            this._unlockedFood.add(Integer.valueOf(u));
        }
        if (this._unlockedFood.size() == 1 && (Integer)this._unlockedFood.get(0) == -1) {
            this._unlockedFood.clear();
        }
        for (String u : unlock = info[73].split(";")) {
            this._unlockedItem.add(Integer.valueOf(u));
        }
        if (this._unlockedItem.size() == 1 && (Integer)this._unlockedItem.get(0) == -1) {
            this._unlockedItem.clear();
        }
        this.setCurrentUses(this._startingUses);
        if (!this._canDecUses) {
            this._currentUses = this._maxUses;
        }
    }

    public void unlockFood(PhysicalState digimon) {
        this.unlockConsumable(digimon, Enum.State.UnlockFood);
    }
}

