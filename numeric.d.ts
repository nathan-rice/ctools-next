declare module numeric {
    export function dot(a: number[] | number[][], b: number[] | number[][]): number | number[] | number[][];

    export function transpose(a: number[] | number[][]): number[] | number[][]
}