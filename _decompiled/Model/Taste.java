/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Model.Config;
import Model.Rank;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

public class Taste<T> {
    private final ArrayList<T> _validLiked;
    private final ArrayList<T> _validDisliked;
    private boolean _unlockedFav;
    private boolean _unlockedDislike;
    private final T _none;
    private int _rankChange;
    private T _preference;
    private T _aversion;
    private T _favorite;
    private T _disliked;
    private ArrayList<T> _intolerant;
    private final Map<T, Rank> _ranks;

    public boolean getUnlockedFav() {
        return this._unlockedFav || this._favorite == this._none;
    }

    public void setUnlockedFav(boolean b) {
        this._unlockedFav = b;
    }

    public boolean getUnlockedDislike() {
        return this._unlockedDislike || this._disliked == this._none;
    }

    public void setUnlockedDislike(boolean b) {
        this._unlockedDislike = b;
    }

    public void setRankChange(int rankChange) {
        this._rankChange = rankChange;
    }

    public ArrayList<T> getIntolerant() {
        return this._intolerant;
    }

    public void setIntolerant(ArrayList<T> i) {
        this._intolerant = i;
    }

    public Map<T, Rank> getRanks() {
        return this._ranks;
    }

    public Rank getRank(T key) {
        return this._ranks.get(key);
    }

    public T getPreference() {
        return this._preference;
    }

    public void setPreference(T p) {
        this._preference = p;
    }

    public T getAversion() {
        return this._aversion;
    }

    public void setAversion(T a) {
        this._aversion = a;
    }

    public T getFavorite() {
        return this._favorite;
    }

    public void setFavorite(T f) {
        if (this._favorite != f) {
            this.checkFavRankOnChange(f);
        }
        this._favorite = f;
    }

    public T getDisliked() {
        return this._disliked;
    }

    public void setDisliked(T d) {
        if (this._disliked != d) {
            this.checkDislikedRankOnChange(d);
        }
        this._disliked = d;
    }

    public Taste(T[] values, ArrayList<T> validLiked, ArrayList<T> validDisliked, T none) {
        HashMap<T, Rank> map = new HashMap<T, Rank>();
        for (T t : values) {
            map.put(t, new Rank());
        }
        this._ranks = map;
        this._validLiked = validLiked;
        this._validDisliked = validDisliked;
        this._none = none;
        this._favorite = none;
        this._disliked = none;
        this._preference = none;
        this._aversion = none;
    }

    public void resetRanks() {
        for (Map.Entry<T, Rank> entry : this._ranks.entrySet()) {
            entry.getValue().setRank(0);
        }
    }

    public void decRankAndCheckFavDislikeChange(T rank, int change) {
        this._ranks.get(rank).decRank(change);
        this.setNewFavDislike(rank);
    }

    private void decRankExcept(T[] exceptions, int change, int min) {
        for (Map.Entry<T, Rank> entry : this._ranks.entrySet()) {
            boolean dec = true;
            for (T e : exceptions) {
                if (entry.getKey() != e) continue;
                dec = false;
                break;
            }
            if (!dec) continue;
            int value = entry.getValue().getRank();
            if (value - change >= min) {
                entry.getValue().decRank(change);
                continue;
            }
            if (value <= min) continue;
            entry.getValue().setRank(min);
        }
    }

    private void incRankExcept(T[] exceptions, int change, int max) {
        for (Map.Entry<T, Rank> entry : this._ranks.entrySet()) {
            boolean inc = true;
            for (T e : exceptions) {
                if (entry.getKey() != e) continue;
                inc = false;
                break;
            }
            if (!inc) continue;
            int value = entry.getValue().getRank();
            if (value + change <= max) {
                entry.getValue().incRank(change);
                continue;
            }
            if (value >= max) continue;
            entry.getValue().setRank(max);
        }
    }

    private void checkRankExcept(T exclude, boolean disliked) {
        for (Map.Entry<T, Rank> entry : this._ranks.entrySet()) {
            if (entry.getKey() == exclude) continue;
            if (disliked) {
                entry.getValue().resetDislikedRank();
                continue;
            }
            entry.getValue().resetFavRank();
        }
    }

    private void checkFavRankOnChange(T rank) {
        this._ranks.get(rank).setRank(Config._rankLimit);
        this.checkRankExcept(rank, false);
    }

    private void checkDislikedRankOnChange(T rank) {
        this._ranks.get(rank).setRank(Config._rankMinimum);
        this.checkRankExcept(rank, true);
    }

    private void changeIntolerantRank(T rank) {
        if (this._intolerant != null && this._intolerant.contains(rank)) {
            this._ranks.get(rank).incRank(Config._rankChangeIntolerant);
        }
    }

    public void changeRank(T check) {
        int rank = 0;
        rank += this._rankChange;
        if (check == this._preference) {
            rank += Config._rankChangeSpeciesPreferenceInc;
        } else if (check == this._aversion) {
            rank -= Config._rankChangeSpeciesPreferenceInc;
        }
        if (check == this._disliked) {
            rank += Config._rankChangeDisliked;
            this.incRankExcept(new Object[]{check, this._none}, Config._rankChangeAfterFav, 0);
            this._ranks.get(this._none).setRank(0);
        } else {
            this._ranks.get(this._none).decRank(this._rankChange);
        }
        if (this._favorite == check) {
            this.decRankExcept(new Object[]{check, this._none}, Config._rankChangeAfterFav, 0);
        }
        this._ranks.get(check).incRank(rank);
        this.changeIntolerantRank(check);
        this.setNewFavDislike(check);
    }

    private void setNewFavDislike(T rank) {
        List<T> list = this.checkFavDislikeChange(rank);
        T fav = list.get(0);
        T dislike = this.checkNoneDislikeChange(this._none);
        dislike = this.getDisliked() == list.get(1) ? dislike : list.get(1);
        this.setFavorite(fav);
        this.setDisliked(dislike);
    }

    private T checkNoneDislikeChange(T noneRank) {
        if (this._disliked != noneRank) {
            return this.checkDislikeChange(noneRank);
        }
        return this._disliked;
    }

    private List<T> checkFavDislikeChange(T rank) {
        T fav = this._favorite;
        T dislike = this._disliked;
        T newValue = this.checkFavChange(rank);
        if (newValue != this._favorite) {
            dislike = this.checkRepeatFav(this._disliked, newValue, this._aversion, this.getValidList(this._validDisliked));
            fav = newValue;
        } else {
            newValue = this.checkDislikeChange(rank);
            if (newValue != this._disliked) {
                fav = this.checkRepeatFav(this._favorite, newValue, this._preference, this.getValidList(this._validLiked));
                dislike = newValue;
            }
        }
        return Arrays.asList(fav, dislike);
    }

    private T checkFavChange(T rank) {
        if (this._ranks.get(rank).favoriteChanged() && this._favorite != rank && this.getValidList(this._validLiked).contains(rank)) {
            return rank;
        }
        return this._favorite;
    }

    private T checkDislikeChange(T rank) {
        if (this._ranks.get(rank).dislikeChanged() && this._disliked != rank && this.getValidList(this._validDisliked).contains(rank)) {
            return rank;
        }
        return this._disliked;
    }

    private T checkRepeatFav(T opposite, T newValue, T firstChoice, ArrayList<T> valid) {
        if (opposite == newValue) {
            if (newValue != firstChoice && valid.contains(firstChoice)) {
                return firstChoice;
            }
            ArrayList<T> list = new ArrayList<T>(valid);
            list.remove(newValue);
            Random r = new Random();
            return list.get(r.nextInt(list.size()));
        }
        return opposite;
    }

    private ArrayList<T> getValidList(ArrayList<T> list) {
        if (this._intolerant != null) {
            ArrayList<T> valid = new ArrayList<T>(list);
            valid.removeAll(this._intolerant);
            return valid;
        }
        return list;
    }
}

