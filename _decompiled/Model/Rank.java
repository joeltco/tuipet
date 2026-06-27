/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Model.Config;

public class Rank {
    private int _rank;

    public int getRank() {
        return this._rank;
    }

    public void setRank(int newRank) {
        this._rank = newRank < Config._rankMinimum ? Config._rankMinimum : (newRank > Config._rankLimit ? Config._rankLimit : newRank);
    }

    public void decRank(int rank) {
        this.setRank(this._rank - rank);
    }

    public void incRank(int rank) {
        this.setRank(this._rank + rank);
    }

    public void resetFavRank() {
        if (this._rank > 0) {
            this._rank = 0;
        }
    }

    public void resetDislikedRank() {
        if (this._rank < 0) {
            this._rank = 0;
        }
    }

    public boolean favoriteChanged() {
        return this._rank >= Config._rankLimit;
    }

    public boolean dislikeChanged() {
        return this._rank <= Config._rankMinimum;
    }
}

