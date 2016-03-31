/**
 * Created by nathan on 3/22/16.
 */

define(["ctools"], function (ctools) {

    describe("Point", function() {
        it("should be properly converted to a 3D array", function() {
            var point = new ctools.Point(30, 30, 10);
            expect(point.to3DArray()).toEqual([30, 30, 10]);
        });

        it("should be properly converted to a 2D array", function () {
            var point = new ctools.Point(30, 30, 10);
            expect(point.to2DArray()).toEqual([30, 30]);
        })
    });

    describe("BezierSurface", function () {

        it("should properly map Point x values to the X array", function () {
            var points = [
                [new ctools.Point(1, 2, 3), new ctools.Point(4, 5, 6)],
                [new ctools.Point(7, 8, 9), new ctools.Point(10, 11, 12)]
            ],
                surface = new ctools.BezierSurface(points);
            expect(surface.x()).toEqual([[1, 4], [7, 10]]);
        });

        it("should properly map Point y values to the y array", function () {
            var points = [
                [new ctools.Point(1, 2, 3), new ctools.Point(4, 5, 6)],
                [new ctools.Point(7, 8, 9), new ctools.Point(10, 11, 12)]
            ],
                surface = new ctools.BezierSurface(points);
            expect(surface.y()).toEqual([[2, 5], [8, 11]]);
        });

        it("should properly map Point z values to the z array", function () {
            var points = [
                [new ctools.Point(1, 2, 3), new ctools.Point(4, 5, 6)],
                [new ctools.Point(7, 8, 9), new ctools.Point(10, 11, 12)]
            ],
                surface = new ctools.BezierSurface(points);
            expect(surface.z()).toEqual([[3, 6], [9, 12]]);
        });

        it("should generate the correct translation matrix", function () {
            var p = [
                new ctools.Point(5, 5),
                new ctools.Point(0, 10),
                new ctools.Point(15, 15),
                new ctools.Point(10, 20)
            ],
                surface = new ctools.BezierSurface([p.slice(0, 2), p.slice(2)]),
                pointArr = p.map(function (point) { return point.toAugmented2DArray()}),
                matrix = surface.generateTranslationMatrix(),
                translated = numeric.dot(pointArr, matrix);

            expect(translated[0][0]).toBeCloseTo(0);
            expect(translated[0][1]).toBeCloseTo(0);
        });

        it("should generate the correct rotation matrix", function () {
            var p = [
                new ctools.Point(0, 0),
                new ctools.Point(-10, 10),
                new ctools.Point(10, 10),
                new ctools.Point(20, 20)
            ],
                surface = new ctools.BezierSurface([p.slice(0, 2), p.slice(2)]),
                pointArr = p.map(function (point) { return point.toAugmented2DArray()}),
                matrix = surface.generateRotationMatrix(),
                rotated = numeric.dot(pointArr, matrix);

            expect(rotated[1][0]).toBeCloseTo(0);
            expect(rotated[2][1]).toBeCloseTo(0);
        });

        it("should properly rotate when projecting to the unit square", function () {
            var p = [
                new ctools.Point(0, 0),
                new ctools.Point(-10, 10),
                new ctools.Point(10, 10),
                new ctools.Point(0, 20)
            ],
                surface = new ctools.BezierSurface([p.slice(0, 2), p.slice(2)]),
                projected = surface.projectToUnitSquare(p);

            expect(projected[0][0]).toBeCloseTo(0);
            expect(projected[0][1]).toBeCloseTo(0);
            expect(projected[1][0]).toBeCloseTo(0);
            expect(projected[1][1]).toBeCloseTo(1);
            expect(projected[2][0]).toBeCloseTo(1);
            expect(projected[2][1]).toBeCloseTo(0);
            expect(projected[3][0]).toBeCloseTo(1);
            expect(projected[3][1]).toBeCloseTo(1);
        });

        it("should properly translate when projecting to the unit square", function () {
            var p = [
                new ctools.Point(10, 10),
                new ctools.Point(0, 20),
                new ctools.Point(20, 20),
                new ctools.Point(10, 30)
            ],
                surface = new ctools.BezierSurface([p.slice(0, 2), p.slice(2)]),
                projected = surface.projectToUnitSquare(p);

            expect(projected[0][0]).toBeCloseTo(0);
            expect(projected[0][1]).toBeCloseTo(0);
            expect(projected[1][0]).toBeCloseTo(0);
            expect(projected[1][1]).toBeCloseTo(1);
            expect(projected[2][0]).toBeCloseTo(1);
            expect(projected[2][1]).toBeCloseTo(0);
            expect(projected[3][0]).toBeCloseTo(1);
            expect(projected[3][1]).toBeCloseTo(1);
        });

        it("should properly scale axes independently when projecting to the unit square", function () {
            var p = [
                new ctools.Point(0, 0),
                new ctools.Point(-5, 5),
                new ctools.Point(10, 10),
                new ctools.Point(5, 15)
            ],
                surface = new ctools.BezierSurface([p.slice(0, 2), p.slice(2)]),
                projected = surface.projectToUnitSquare(p);

            expect(projected[0][0]).toBeCloseTo(0);
            expect(projected[0][1]).toBeCloseTo(0);
            expect(projected[1][0]).toBeCloseTo(0);
            expect(projected[1][1]).toBeCloseTo(1);
            expect(projected[2][0]).toBeCloseTo(1);
            expect(projected[2][1]).toBeCloseTo(0);
            expect(projected[3][0]).toBeCloseTo(1);
            expect(projected[3][1]).toBeCloseTo(1);
        });

        it("should properly compute the bezier surface z value", function () {
            var p = [
                new ctools.Point(0, 0, 10),
                new ctools.Point(-5, 5, 0),
                new ctools.Point(10, 10, 10),
                new ctools.Point(5, 15, 0)
            ],
                surface = new ctools.BezierSurface([p.slice(0, 2), p.slice(2)]);

            expect(surface.evaluate(0, 0)).toBeCloseTo(10);
            expect(surface.evaluate(0, 1)).toBeCloseTo(0);
            expect(surface.evaluate(1, 0)).toBeCloseTo(10);
            expect(surface.evaluate(1, 1)).toBeCloseTo(0);
        });

    })
});


