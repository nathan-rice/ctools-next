/// <reference path="numeric.d.ts" />

const quadraticBernsteinMatrix = [
    [1, 0, 0, 0],
    [-3, 3, 0, 0],
    [3, -6, 3, 0],
    [-1, 3, -3, 1]
];

const quadraticBernsteinMatrixTranspose = [
    [1, -3, 3, -1],
    [0, 3, -6, 3],
    [0, 0, 3, -3],
    [0, 0, 0, 1]
];

const linearBernsteinMatrixTranspose = [
    [1, -1],
    [0, 1]
];

// Precomputed factorial values
const fact = [1, 1, 2, 6, 24];

const pow = Math.pow;

class Point {
    constructor(public x, public y, public z) {}
}

class BezierSurface {
    interpolationX: number[][];
    interpolationY: number[][];
    interpolationZ: number[][];

    protected m = 3;
    protected n = 1;

    constructor(public controlPoints: Point[][]) {
        this.generateInterpolationMatrices();
    }

    protected generateInterpolationMatrix(points: number[][]) {
        let i, j, p;

        // we need to apply the binomial coefficients to the points
        for (i = points.length; i--;) {
            for (j = points[i].length; j--;) {
                // the binomial coefficient here has been simplified since j will never exceed 1
                points[i][j] = points[i][j] * 12 / fact[i] / fact[3 - i]
            }
        }
        p = numeric.dot(points, linearBernsteinMatrixTranspose);
        p = numeric.dot(quadraticBernsteinMatrix, p);
        return p;
    }

    protected generateInterpolationMatrices() {
        this.interpolationX = this.generateInterpolationMatrix(this.x());
        this.interpolationY = this.generateInterpolationMatrix(this.y());
        this.interpolationZ = this.generateInterpolationMatrix(this.z());
    }

    evaluate(u, v) {
        let uArr = [1, u, pow(u, 2), pow(u, 3)], vArr = [1, v];
        return numeric.dot(numeric.dot(uArr, this.interpolationZ) as number[][], numeric.transpose(vArr));
    }

    projectToUnitSquare(points: number[][]) {
        // first we need to define a linear transformation
    }

    x(): number[][] {
        return this.controlPoints.map(a => a.map(p => p.x));
    }

    y(): number[][] {
        return this.controlPoints.map(a => a.map(p => p.y));
    }

    z(): number[][] {
        return this.controlPoints.map(a => a.map(p => p.z));
    }
}

class BicubicBezierSurface extends BezierSurface {
    protected generateInterpolationMatrix(points: number[][]) {
        let i, j, p;

        // we need to apply the binomial coefficients to the points
        for (i = points.length; i--;) {
            for (j = points[i].length; j--;) {
                points[i][j] = points[i][j] * 12 / fact[i] / fact[j] / fact[3 - i] / fact[3 - j]
            }
        }
        p = numeric.dot(points, quadraticBernsteinMatrixTranspose);
        p = numeric.dot(quadraticBernsteinMatrix, p);
        return p;
    }
}