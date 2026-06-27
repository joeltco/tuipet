/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Controller.Utility;
import Model.Consumable;
import Model.Enum;
import Model.FoodType;
import Model.Item;
import java.util.ArrayList;

public class ShopConsumable {
    private final int _id;
    private final int _price;
    private int _salePrice;
    private final int _consumableID;
    private final boolean _isFood;
    private final byte[] _stockChance;
    private final byte[] _saleChance;
    private final byte _saleFactor;
    private final byte _resellFactor;
    private final boolean _mustStock;
    private final byte _maxStock;
    private final byte _minStock;
    private byte _currentStock;
    private final ArrayList<byte[]> _timeAvailable;

    public int getID() {
        return this._id;
    }

    public int getPrice() {
        return this._price;
    }

    public int getSalePrice() {
        return this._salePrice;
    }

    public void setSalePrice(int i) {
        this._salePrice = i;
    }

    public int getConsumableID() {
        return this._consumableID;
    }

    public boolean isFood() {
        return this._isFood;
    }

    public byte[] getStockChance() {
        return this._stockChance;
    }

    public byte[] getSaleChance() {
        return this._saleChance;
    }

    public byte getSaleFactor() {
        return this._saleFactor;
    }

    public byte getResellFactor() {
        return this._resellFactor;
    }

    public boolean mustStock() {
        return this._mustStock;
    }

    public byte getMaxStock() {
        return this._maxStock;
    }

    public byte getMinStock() {
        return this._minStock;
    }

    public byte getCurrentStock() {
        return this._currentStock;
    }

    public void setCurrentStock(int i) {
        if (this._currentStock > -1) {
            this._currentStock = i < 0 ? (byte)0 : (i > this._maxStock ? this._maxStock : (byte)i);
        }
    }

    public void decStock(int i) {
        this.setCurrentStock(this._currentStock - i);
    }

    public boolean isAvailable() {
        return this._currentStock > 0 || this._currentStock == -1;
    }

    public boolean withinTime(byte currentHour, Enum.Season s) {
        byte[] time = this._timeAvailable.get(s.ordinal());
        return currentHour >= time[0] && currentHour <= time[1];
    }

    public ArrayList<byte[]> getTimeAvailable() {
        return this._timeAvailable;
    }

    public ShopConsumable(int consumableID, boolean isFood, byte[] stockChance, byte maxStock, byte minStock, ArrayList<byte[]> timeAvailable, int price, boolean mustStock, byte[] saleChance, byte saleFactor, byte resellFactor) {
        this(-1, consumableID, isFood, stockChance, maxStock, minStock, timeAvailable, price, mustStock, saleChance, saleFactor, resellFactor);
    }

    public ShopConsumable(int id, int consumableID, boolean isFood, byte[] stockChance, byte maxStock, byte minStock, ArrayList<byte[]> timeAvailable, int price, boolean mustStock, byte[] saleChance, byte saleFactor, byte resellFactor) {
        this._id = id;
        this._consumableID = consumableID;
        this._isFood = isFood;
        this._stockChance = stockChance;
        this._maxStock = maxStock;
        this._minStock = minStock;
        this._timeAvailable = timeAvailable;
        this._price = price;
        this._mustStock = mustStock;
        this._saleChance = saleChance;
        this._saleFactor = saleFactor;
        this._resellFactor = resellFactor;
    }

    public ShopConsumable(String[] data) {
        this._id = Integer.parseInt(data[0]);
        this._consumableID = Integer.parseInt(data[1]);
        this._isFood = Boolean.parseBoolean(data[2]);
        this._minStock = Byte.parseByte(data[3]);
        this._maxStock = Byte.parseByte(data[4]);
        String[] s = data[5].split(";");
        this._stockChance = new byte[]{Byte.parseByte(s[0]), Byte.parseByte(s[1]), Byte.parseByte(s[2]), Byte.parseByte(s[3])};
        String[] ranges = data[6].split(";");
        this._timeAvailable = new ArrayList();
        for (String r : ranges) {
            String[] time = r.split("t");
            this._timeAvailable.add(new byte[]{Byte.parseByte(time[0]), Byte.parseByte(time[1])});
        }
        this._price = Integer.parseInt(data[7]);
        this._mustStock = Boolean.parseBoolean(data[8]);
        s = data[9].split(";");
        this._saleChance = new byte[]{Byte.parseByte(s[0]), Byte.parseByte(s[1]), Byte.parseByte(s[2]), Byte.parseByte(s[3])};
        this._saleFactor = Byte.parseByte(data[10]);
        this._resellFactor = Byte.parseByte(data[11]);
    }

    public final void randomizeStock() {
        this._currentStock = this._minStock;
        if (this._minStock > 0 && this._minStock < this._maxStock) {
            this._currentStock = (byte)Utility.randomBetween(this._minStock, this._maxStock);
        }
    }

    public FoodType getFood(ArrayList<FoodType> f) {
        return this._consumableID != -1 ? f.get(this._consumableID) : null;
    }

    public Item getItem(ArrayList<Item> i) {
        return this._consumableID != -1 ? i.get(this._consumableID) : null;
    }

    public Consumable getConsumable(ArrayList<Consumable> c) {
        return this._consumableID != -1 ? c.get(this._consumableID) : null;
    }

    public boolean checkSale(Enum.Season s) {
        this.endSale();
        boolean sale = Utility.randomChance(this._saleChance[s.ordinal()], 100);
        if (sale) {
            this._salePrice = this._price - this._price / this._saleFactor;
        }
        return sale;
    }

    public void endSale() {
        this._salePrice = 0;
    }

    public boolean isSale() {
        return this._salePrice > 0;
    }

    public int getPurchasePrice() {
        return this.isSale() ? this._salePrice : this._price;
    }

    public int getResellPrice() {
        if (this._resellFactor == 0) {
            return 0;
        }
        return this._price / this._resellFactor;
    }

    public int getResellPricePerUse(Consumable c, int quantity) {
        double pricePerUse = (double)this.getResellPrice() / (double)c.getUsesPerConsumable();
        double q = (double)quantity * (double)c.getUsesPerConsumable();
        if (q <= (double)c.getCurrentUses()) {
            return (int)(q * pricePerUse);
        }
        return (int)((double)c.getCurrentUses() * pricePerUse);
    }
}

