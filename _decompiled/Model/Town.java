/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Controller.Utility;
import Model.BackgroundRange;
import Model.Consumable;
import Model.FoodType;
import Model.Item;
import Model.PhysicalState;
import Model.ShopConsumable;
import java.util.ArrayList;

public class Town {
    private int _id;
    private BackgroundRange _backgroundRange;
    private String _smallTownIcon;
    private ArrayList<ShopConsumable> _itemOverride = new ArrayList();
    private ArrayList<ShopConsumable> _foodOverride = new ArrayList();
    private byte _itemInventoryMax;
    private byte _foodInventoryMax;
    private ArrayList<ShopConsumable> _itemShop = new ArrayList();
    private ArrayList<ShopConsumable> _foodShop = new ArrayList();
    private int[] _trophies;
    private ArrayList<byte[]> _foodShopTime;
    private ArrayList<byte[]> _itemShopTime;
    private ArrayList<byte[]> _habitatShopTime;
    private boolean _canSellItems;
    private boolean _canSellFood;
    private int _tournamentLimit;
    private int[] _forcedTrophies;
    private boolean _unlocked;

    public int getID() {
        return this._id;
    }

    public BackgroundRange getBackgroundRange() {
        return this._backgroundRange;
    }

    public String getSmallTownIcon() {
        return this._smallTownIcon;
    }

    public ArrayList<ShopConsumable> getFoodOverride() {
        return this._foodOverride;
    }

    public ArrayList<ShopConsumable> getItemOverride() {
        return this._itemOverride;
    }

    public byte getFoodInventoryMax() {
        return this._foodInventoryMax;
    }

    public byte getItemInventoryMax() {
        return this._itemInventoryMax;
    }

    public boolean isUnlocked() {
        return this._unlocked;
    }

    public void setUnlocked(boolean b) {
        this._unlocked = b;
    }

    public int getTournamentLimit() {
        return this._tournamentLimit;
    }

    public int[] getForcedTrophies() {
        return this._forcedTrophies;
    }

    public ArrayList<ShopConsumable> getItemShop(PhysicalState digimon) {
        if (this._itemShop.isEmpty()) {
            this._itemShop = digimon.randomizeItemShop(this._itemOverride, this._itemInventoryMax, false);
        }
        return this._itemShop;
    }

    public ArrayList<ShopConsumable> getItemShop() {
        return this._itemShop;
    }

    public void setItemShop(ArrayList<Item> items) {
        this._itemShop.clear();
        for (Item f : items) {
            this._itemShop.add(this.compareConsumables(f, this._itemOverride, false));
        }
    }

    public ArrayList<ShopConsumable> getFoodShop(PhysicalState digimon) {
        if (this._foodShop.isEmpty()) {
            this._foodShop = digimon.randomizeFoodShop(this._foodOverride, this._foodInventoryMax, false);
        }
        return this._foodShop;
    }

    public ArrayList<ShopConsumable> getFoodShop() {
        return this._foodShop;
    }

    public void setFoodShop(ArrayList<FoodType> foods) {
        this._foodShop.clear();
        for (FoodType f : foods) {
            this._foodShop.add(this.compareConsumables(f, this._foodOverride, true));
        }
    }

    public int[] getTrophies(PhysicalState digimon) {
        if (this._trophies == null) {
            this.randomizeTrophies(digimon);
        }
        return this._trophies;
    }

    public int[] getTrophies() {
        return this._trophies;
    }

    public void setTrophies(int[] trophies) {
        this._trophies = new int[this._tournamentLimit];
        for (int i = 0; i < trophies.length; ++i) {
            this._trophies[i] = trophies[i];
        }
    }

    public boolean getCanSellFood() {
        return this._canSellFood;
    }

    public boolean getCanSellItems() {
        return this._canSellItems;
    }

    public ArrayList<byte[]> getFoodShopTime() {
        return this._foodShopTime;
    }

    public ArrayList<byte[]> getItemShopTime() {
        return this._itemShopTime;
    }

    public ArrayList<byte[]> getHabitatShopTime() {
        return this._habitatShopTime;
    }

    public Town(String[] data, ArrayList<ShopConsumable> consumables) {
        String[] time;
        this._id = Integer.parseInt(data[0]);
        String[] range = data[1].split("t");
        this._backgroundRange = new BackgroundRange(Integer.parseInt(data[2]), new int[]{Integer.parseInt(range[0]), Integer.parseInt(range[1])});
        this._smallTownIcon = data[3];
        if (consumables.size() > 0) {
            String[] i = data[4].split(":");
            this._itemOverride = Utility.getConsumableID(i, consumables);
        }
        if (consumables.size() > 0) {
            String[] f = data[5].split(":");
            this._foodOverride = Utility.getConsumableID(f, consumables);
        }
        this._foodInventoryMax = Byte.parseByte(data[6]);
        this._itemInventoryMax = Byte.parseByte(data[7]);
        this._canSellItems = Boolean.parseBoolean(data[8]);
        this._canSellFood = Boolean.parseBoolean(data[9]);
        String[] ranges = data[10].split(";");
        this._foodShopTime = new ArrayList();
        for (String r : ranges) {
            time = r.split("t");
            this._foodShopTime.add(new byte[]{Byte.parseByte(time[0]), Byte.parseByte(time[1])});
        }
        ranges = data[11].split(";");
        this._itemShopTime = new ArrayList();
        for (String r : ranges) {
            time = r.split("t");
            this._itemShopTime.add(new byte[]{Byte.parseByte(time[0]), Byte.parseByte(time[1])});
        }
        ranges = data[12].split(";");
        this._habitatShopTime = new ArrayList();
        for (String r : ranges) {
            time = r.split("t");
            this._habitatShopTime.add(new byte[]{Byte.parseByte(time[0]), Byte.parseByte(time[1])});
        }
        this._unlocked = Boolean.parseBoolean(data[13]);
        int tournamentLimit = Integer.parseInt(data[14]);
        String[] trophies = data[15].split(";");
        if (trophies.length > 0 && !trophies[0].equals("-1")) {
            tournamentLimit += trophies.length;
            this._forcedTrophies = new int[trophies.length];
            for (int i = 0; i < trophies.length; ++i) {
                this._forcedTrophies[i] = Integer.parseInt(trophies[i]);
            }
        }
        this._tournamentLimit = tournamentLimit;
    }

    private ShopConsumable compareConsumables(Consumable c, ArrayList<ShopConsumable> override, boolean isFood) {
        ShopConsumable d = c.getHomeShop();
        if (!override.isEmpty()) {
            for (ShopConsumable o : override) {
                if (o.getID() != c.getID()) continue;
                d = o;
                break;
            }
        }
        return new ShopConsumable(c.getID(), isFood, d.getStockChance(), d.getMaxStock(), d.getMinStock(), d.getTimeAvailable(), d.getPrice(), d.mustStock(), d.getSaleChance(), d.getSaleFactor(), d.getResellFactor());
    }

    private ShopConsumable getOverrideConsumable(int id, ArrayList<ShopConsumable> list) {
        for (ShopConsumable c : list) {
            if (c.getID() != id) continue;
            return c;
        }
        return null;
    }

    public ShopConsumable getOverrideFood(int id) {
        return this.getOverrideConsumable(id, this._foodOverride);
    }

    public ShopConsumable getOverrideItem(int id) {
        return this.getOverrideConsumable(id, this._itemOverride);
    }

    public ArrayList<ShopConsumable> restockItemShop(PhysicalState digimon) {
        if (!this._itemShop.isEmpty()) {
            return digimon.restockItemShop(this._itemOverride, this._itemShop, this._itemInventoryMax, false);
        }
        return this._itemShop;
    }

    public ArrayList<ShopConsumable> restockFoodShop(PhysicalState digimon) {
        if (!this._foodShop.isEmpty()) {
            return digimon.restockFoodShop(this._foodOverride, this._foodShop, this._foodInventoryMax, false);
        }
        return this._foodShop;
    }

    public void resetDailyShops() {
        this._foodShop.clear();
        this._itemShop.clear();
        this._trophies = null;
    }

    public void randomizeTrophies(PhysicalState digimon) {
        this._trophies = digimon.getTournament().randTrophyIDs(digimon.getSeason(), new int[this._tournamentLimit], this._forcedTrophies);
    }

    public int getStartingLocation() {
        return this._backgroundRange.getRange()[0];
    }

    public int getEndingLocation() {
        return this._backgroundRange.getRange()[1];
    }
}

