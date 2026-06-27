/*
 * Decompiled with CFR 0.152.
 */
package View;

import javax.swing.JPanel;

public class DisplayPane
extends JPanel {
    public DisplayPane() {
        this(true);
    }

    public DisplayPane(boolean opaque) {
        this.setLayout(null);
        this.setVisible(true);
        this.setOpaque(opaque);
    }
}

