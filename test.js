/**
 * Created by nathan on 3/22/16.
 */

define(["demo"], function (demo) {
    describe("Point", function() {
        it("should be properly converted to a 3D array", function() {
            var point = new demo.Point(30, 30, 10);
            expect(point.to3DArray()).toEqual([30, 30, 10]);
        });

        it("should be properly converted to a 2D array", function () {
            var point = new demo.Point(30, 30, 10);
            expect(point.to2DArray()).toEqual([30, 30]);
        })
    });

    describe("BezierSurface", function () {

        it("should properly map Point x values to the X array", function () {
            var points = [
                [new demo.Point(1, 2, 3), new demo.Point(4, 5, 6)],
                [new demo.Point(7, 8, 9), new demo.Point(10, 11, 12)]
            ],
                surface = new demo.BezierSurface(points);
            expect(surface.x()).toEqual([[1, 4], [7, 10]]);
        });

        it("should properly map Point y values to the y array", function () {
            var points = [
                [new demo.Point(1, 2, 3), new demo.Point(4, 5, 6)],
                [new demo.Point(7, 8, 9), new demo.Point(10, 11, 12)]
            ],
                surface = new demo.BezierSurface(points);
            expect(surface.y()).toEqual([[2, 5], [8, 11]]);
        });

        it("should properly map Point z values to the z array", function () {
            var points = [
                [new demo.Point(1, 2, 3), new demo.Point(4, 5, 6)],
                [new demo.Point(7, 8, 9), new demo.Point(10, 11, 12)]
            ],
                surface = new demo.BezierSurface(points);
            expect(surface.z()).toEqual([[3, 6], [9, 12]]);
        });

        it("should properly rotate when projecting to the unit square", function () {
            var points = [
                [new demo.Point(0, 0), new demo.Point(-10, 10)],
                [new demo.Point(10, 10), new demo.Point(0, 20)]
            ],
                surface = new demo.BezierSurface(points),
                projected = surface.projectToUnitSquare(points[0]);

            expect(projected[0][0]).toBeCloseTo(0);
            expect(projected[0][1]).toBeCloseTo(0);
            expect(projected[1][0]).toBeCloseTo(0);
            expect(projected[1][1]).toBeCloseTo(1);
        });

    })
});


