package com.vasworks.android.util;

/**
 * Key and Value
 */
public class Triplet {
    public String key;
    public String value;
    public String value2;

    /**
     * @param key
     * @param value
     */
    public Triplet(final String key, final String value, final String value2) {
        super();
        this.key = key;
        this.value = value;
        this.value2 = value2;
    }

	@Override
	public String toString() {
		return value + " (" + value2 + ")";
	}

}