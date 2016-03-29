interface IRBush {
    constructor;
    insert(entry: [number, number, number, number, any] | Object);
    remove(entry: [number, number, number, number, any] | Object);
    load(entries: [number, number, number, number, any][] | Object[]);
    search(boundary: [number, number, number, number, any]): [number, number, number, number, any][];
    collides(boundary: [number, number, number, number, any]): [number, number, number, number, any][];
    all(): [number, number, number, number, any][];
}

declare function rbush(maxNodeEntries: number, accessors?: string[]): IRBush;