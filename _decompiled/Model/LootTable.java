/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Controller.Utility;
import Model.ConsumableDrops;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

public class LootTable {
    private final String MOD_FOLDER;
    private final String MODEL_FOLDER;
    private Map<Integer, ConsumableDrops[]> _lootTable;

    public Map<Integer, ConsumableDrops[]> getLootTable() {
        return this._lootTable;
    }

    public LootTable(String mod, String model) {
        this.MOD_FOLDER = mod;
        this.MODEL_FOLDER = model;
        this._lootTable = new HashMap<Integer, ConsumableDrops[]>();
        ConsumableDrops[] drops = this.readDrops();
        try (InputStream in = Utility.getInputStream(this.MOD_FOLDER, this.MODEL_FOLDER, "lootTable.csv");
             BufferedReader reader = new BufferedReader(new InputStreamReader(in));){
            String line = reader.readLine();
            while ((line = reader.readLine()) != null) {
                this.readInfo(line.split(","), drops);
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    /*
     * Enabled aggressive exception aggregation
     */
    private ConsumableDrops[] readDrops() {
        try (InputStream in = Utility.getInputStream(this.MOD_FOLDER, this.MODEL_FOLDER, "dropRate.csv");){
            ConsumableDrops[] consumableDropsArray;
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(in));){
                ArrayList<ConsumableDrops> itemDrops = new ArrayList<ConsumableDrops>();
                String line = reader.readLine();
                while ((line = reader.readLine()) != null) {
                    itemDrops.add(new ConsumableDrops(line.split(",")));
                }
                consumableDropsArray = itemDrops.toArray(new ConsumableDrops[itemDrops.size()]);
            }
            return consumableDropsArray;
        }
        catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }

    private void readInfo(String[] info, ConsumableDrops[] drops) {
        int id = Integer.parseInt(info[0]);
        ArrayList<ConsumableDrops> d = new ArrayList<ConsumableDrops>();
        for (int i = 1; i < info.length; ++i) {
            int dropRateID = Integer.parseInt(info[i]);
            d.add(drops[dropRateID]);
        }
        this._lootTable.put(id, d.toArray(new ConsumableDrops[d.size()]));
    }
}

