/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Model.Config;
import Model.Enum;

public class DNA {
    private final int _fieldLength = Enum.Field.values().length - 1;
    private int[] _owned = new int[this._fieldLength];
    private int[] _dna = new int[this._fieldLength];

    public void setOwned(Enum.Field f, int i) {
        if (i > Config._maxDNAInventory) {
            i = Config._maxDNAInventory;
        }
        this._owned[f.ordinal()] = i;
    }

    public int getOwned(Enum.Field f) {
        return this._owned[f.ordinal()];
    }

    public int[] getOwned() {
        return this._owned;
    }

    public int getPercent(Enum.Field f) {
        return (int)(100.0 * ((double)this.getDNA(f) / (double)this.getTotalDNA()));
    }

    public void setDNA(Enum.Field f, int i) {
        this._dna[f.ordinal()] = i;
    }

    public int getDNA(Enum.Field f) {
        return this._dna[f.ordinal()];
    }

    public int[] getDNA() {
        return this._dna;
    }

    public void resetDNA() {
        this._dna = new int[this._fieldLength];
    }

    public int getTotalDNA() {
        int total = 0;
        for (int i : this._dna) {
            total += i;
        }
        return total;
    }

    public Enum.Field getHighestDNA() {
        Enum.Field f = Enum.Field.NA;
        int record = 0;
        int field = -1;
        for (int i = 0; i < this._dna.length; ++i) {
            if (this._dna[i] <= record) continue;
            record = this._dna[i];
            field = i;
        }
        int matches = 0;
        for (int i : this._dna) {
            if (i == record) {
                ++matches;
            }
            if (matches > 1) break;
        }
        if (matches == 1 && field != -1) {
            f = Enum.Field.values()[field];
        }
        return f;
    }

    public void generateDNA(Enum.Field f, int i) {
        int n = f.ordinal();
        int n2 = this._owned[n] + i;
        this._owned[n] = n2;
        this.setOwned(f, n2);
    }

    public boolean applyDNA(Enum.Field f, int quantity) {
        boolean success;
        boolean bl = success = this._owned[f.ordinal()] >= quantity;
        if (success) {
            this._dna[f.ordinal()] = this._dna[f.ordinal()] + quantity;
            this._owned[f.ordinal()] = this._owned[f.ordinal()] - quantity;
        }
        return success;
    }

    public void readInfo(String[] info) {
        for (int i = 0; i < info.length; ++i) {
            if (i < this._fieldLength) {
                this._dna[i] = Integer.parseInt(info[i]);
                continue;
            }
            this._owned[i - this._fieldLength] = Integer.parseInt(info[i]);
        }
    }
}

