# Go (Golang) — Complete Interview & Project Reference

> Read top to bottom once for a full mental model.
> Use as a reference when building or preparing.

---

## Table of Contents

1. [Why Go — Mental Model](#1-why-go--mental-model)
2. [Basics — Types, Variables, Constants](#2-basics--types-variables-constants)
3. [Control Flow](#3-control-flow)
4. [Functions](#4-functions)
5. [Pointers](#5-pointers)
6. [Arrays, Slices, Maps](#6-arrays-slices-maps)
7. [Structs & Methods](#7-structs--methods)
8. [Interfaces](#8-interfaces)
9. [Error Handling](#9-error-handling)
10. [Goroutines & Channels](#10-goroutines--channels)
11. [Concurrency Patterns](#11-concurrency-patterns)
12. [Generics (Go 1.18+)](#12-generics-go-118)
13. [Packages, Modules & Project Structure](#13-packages-modules--project-structure)
14. [Standard Library Essentials](#14-standard-library-essentials)
15. [HTTP Servers & REST APIs](#15-http-servers--rest-apis)
16. [Database Patterns](#16-database-patterns)
17. [Testing](#17-testing)
18. [Common Go Patterns](#18-common-go-patterns)
19. [Performance & Memory](#19-performance--memory)
20. [Interview Questions & Answers](#20-interview-questions--answers)

---

## 1. Why Go — Mental Model

```
Go is designed for:
  Simplicity   — small spec, one way to do most things
  Concurrency  — goroutines are cheap (2KB stack vs 2MB for OS threads)
  Compilation  — compiles to a single static binary, fast build times
  Safety       — garbage collected, no pointer arithmetic, no undefined behavior
  Readability  — gofmt enforces consistent style; explicit over clever

Not designed for:
  Inheritance hierarchies (no classes, no `extends`)
  Operator overloading
  Exceptions (use explicit error returns)
  Generics heavy usage (added in 1.18 but still limited)
```

### Go vs Other Languages

| Feature | Go | Java | Python |
|---|---|---|---|
| Concurrency | goroutines + channels | threads + locks | asyncio / GIL |
| Error handling | explicit return values | exceptions | exceptions |
| Inheritance | composition only | class hierarchy | class hierarchy |
| Memory | GC, no manual alloc | GC | GC |
| Compile | fast, static binary | slow, JVM | interpreted |
| Generics | 1.18+ | yes | duck typing |

---

## 2. Basics — Types, Variables, Constants

### 2.1 Variable Declaration

```go
// Full declaration
var name string = "Alice"
var age int = 30

// Type inferred
var score = 95.5

// Short declaration (inside functions only)
count := 10
message := "hello"

// Multiple variables
x, y, z := 1, 2, 3
var a, b int

// Zero values (no garbage in Go — always initialized)
var i int        // 0
var f float64    // 0.0
var s string     // ""
var b bool       // false
var p *int       // nil
var sl []int     // nil
var m map[string]int  // nil
```

### 2.2 Basic Types

```go
// Integer
int, int8, int16, int32, int64
uint, uint8, uint16, uint32, uint64
uintptr

// Floating point
float32, float64

// Complex
complex64, complex128

// Text
string    // UTF-8 immutable byte sequence
rune      // alias for int32 — represents a Unicode code point
byte      // alias for uint8

// Boolean
bool

// Type aliases
type Celsius    float64
type Fahrenheit float64

func CToF(c Celsius) Fahrenheit {
    return Fahrenheit(c*9/5 + 32)
}
```

### 2.3 Constants & iota

```go
const Pi = 3.14159
const (
    MaxRetries = 3
    Timeout    = 30
)

// iota — auto-incrementing in const block
type Direction int

const (
    North Direction = iota  // 0
    East                    // 1
    South                   // 2
    West                    // 3
)

// iota with expressions
const (
    KB = 1 << (10 * (iota + 1))  // 1024
    MB                            // 1048576
    GB                            // 1073741824
)

// Typed constants enforce type safety
type Weekday int
const (
    Monday Weekday = iota + 1
    Tuesday
    Wednesday
    Thursday
    Friday
    Saturday
    Sunday
)
```

### 2.4 Type Conversion

```go
var i int = 42
var f float64 = float64(i)     // explicit — no implicit conversion in Go
var u uint = uint(f)

// String conversions
import "strconv"
n, err := strconv.Atoi("42")   // string → int
s := strconv.Itoa(42)          // int → string
f, err := strconv.ParseFloat("3.14", 64)
s := strconv.FormatFloat(3.14, 'f', 2, 64)

// byte slice ↔ string (O(n) copy)
bs := []byte("hello")
s := string(bs)

// rune slice ↔ string
rs := []rune("hello, 世界")
fmt.Println(len(rs))  // 9 (characters, not bytes)
```

---

## 3. Control Flow

### 3.1 if / else

```go
// Condition does not need parentheses
if x > 0 {
    fmt.Println("positive")
} else if x < 0 {
    fmt.Println("negative")
} else {
    fmt.Println("zero")
}

// Init statement — variable scoped to if block
if n, err := strconv.Atoi(s); err == nil {
    fmt.Println(n * 2)
} else {
    fmt.Println("error:", err)
}
```

### 3.2 for — the only loop in Go

```go
// Classic C-style
for i := 0; i < 10; i++ {
    fmt.Println(i)
}

// While-style
for n < 100 {
    n *= 2
}

// Infinite loop
for {
    if shouldStop() { break }
}

// Range over slice
fruits := []string{"apple", "banana", "cherry"}
for i, v := range fruits {
    fmt.Printf("%d: %s\n", i, v)
}
for _, v := range fruits { /* ignore index */ }
for i := range fruits    { /* ignore value */ }

// Range over map (unordered)
m := map[string]int{"a": 1, "b": 2}
for k, v := range m {
    fmt.Printf("%s=%d\n", k, v)
}

// Range over string (yields runes, not bytes)
for i, r := range "hello, 世界" {
    fmt.Printf("%d: %c\n", i, r)
}

// Range over channel
for msg := range ch {
    process(msg)
}
```

### 3.3 switch

```go
// No fallthrough by default (unlike C)
switch day {
case Monday, Tuesday:
    fmt.Println("early week")
case Friday:
    fmt.Println("TGIF")
default:
    fmt.Println("midweek")
}

// Switch with no condition (= if/else chain)
switch {
case score >= 90:
    grade = "A"
case score >= 80:
    grade = "B"
default:
    grade = "C"
}

// Type switch
func describe(i interface{}) string {
    switch v := i.(type) {
    case int:
        return fmt.Sprintf("int: %d", v)
    case string:
        return fmt.Sprintf("string: %s", v)
    case bool:
        return fmt.Sprintf("bool: %v", v)
    default:
        return fmt.Sprintf("unknown: %T", v)
    }
}

// Explicit fallthrough
switch n {
case 1:
    fmt.Println("one")
    fallthrough
case 2:
    fmt.Println("one or two")
}
```

### 3.4 defer, goto, labels

```go
// defer — runs when surrounding function returns (LIFO order)
func readFile(path string) (string, error) {
    f, err := os.Open(path)
    if err != nil { return "", err }
    defer f.Close()             // guaranteed cleanup

    // Read and return...
}

// Multiple defers run in LIFO (stack) order
func multi() {
    defer fmt.Println("third")
    defer fmt.Println("second")
    defer fmt.Println("first")  // prints first
}

// defer + named return for cleanup in error path
func mustClose(f *os.File) (err error) {
    defer func() {
        if cerr := f.Close(); cerr != nil && err == nil {
            err = cerr
        }
    }()
    // ... do work
    return nil
}
```

---

## 4. Functions

### 4.1 Basics

```go
func add(a, b int) int {
    return a + b
}

// Multiple return values — idiomatic in Go
func divide(a, b float64) (float64, error) {
    if b == 0 {
        return 0, errors.New("division by zero")
    }
    return a / b, nil
}

result, err := divide(10, 2)
if err != nil {
    log.Fatal(err)
}
```

### 4.2 Named Return Values

```go
func minMax(arr []int) (min, max int) {
    min, max = arr[0], arr[0]
    for _, v := range arr[1:] {
        if v < min { min = v }
        if v > max { max = v }
    }
    return  // naked return — returns named values
}
```

### 4.3 Variadic Functions

```go
func sum(nums ...int) int {
    total := 0
    for _, n := range nums {
        total += n
    }
    return total
}

sum(1, 2, 3)               // 6
nums := []int{1, 2, 3, 4}
sum(nums...)               // spread slice into variadic — 10
```

### 4.4 First-Class Functions & Closures

```go
// Functions as values
type Transformer func(int) int

func apply(nums []int, f Transformer) []int {
    result := make([]int, len(nums))
    for i, v := range nums {
        result[i] = f(v)
    }
    return result
}

doubled := apply([]int{1, 2, 3}, func(n int) int { return n * 2 })

// Closure captures outer variables
func makeCounter() func() int {
    count := 0
    return func() int {
        count++      // captures count from outer scope
        return count
    }
}

counter := makeCounter()
counter() // 1
counter() // 2

// Closure pitfall in loops
funcs := make([]func(), 5)
for i := 0; i < 5; i++ {
    i := i                    // shadow loop var to capture current value
    funcs[i] = func() { fmt.Println(i) }
}
```

### 4.5 defer + panic + recover

```go
func safeDiv(a, b int) (result int, err error) {
    defer func() {
        if r := recover(); r != nil {
            err = fmt.Errorf("recovered from panic: %v", r)
        }
    }()
    return a / b, nil    // panics if b == 0
}

// Panic terminates goroutine (propagates up call stack until recover or crash)
// Use panic only for truly unrecoverable situations
// recover only works inside a deferred function
```

---

## 5. Pointers

```go
var x int = 42
p := &x           // & takes the address
fmt.Println(*p)   // * dereferences — prints 42
*p = 100          // modifies x through pointer
fmt.Println(x)    // 100

// Pointer to struct
type Point struct { X, Y int }
pt := &Point{1, 2}
pt.X = 10         // Go auto-dereferences: pt.X == (*pt).X

// new() allocates, returns pointer
p := new(int)     // *int pointing to zero value 0

// When to use pointers:
// 1. Mutate the argument in a function
// 2. Avoid copying large structs
// 3. Signal "optional" value (nil pointer = no value)
// 4. Methods that need to modify the receiver

func increment(n *int) { *n++ }
x := 5
increment(&x)
fmt.Println(x) // 6

// Pointer vs value receiver — covered in Section 7
```

---

## 6. Arrays, Slices, Maps

### 6.1 Arrays (fixed size, rarely used directly)

```go
var a [3]int           // [0 0 0]
a[0] = 1
b := [3]int{1, 2, 3}
c := [...]int{4, 5, 6} // compiler counts elements

// Arrays are VALUE types — copying is expensive for large arrays
x := b
x[0] = 99             // does NOT affect b
```

### 6.2 Slices (the workhorse of Go)

```go
// Slice = pointer + length + capacity
// nil slice: length=0, capacity=0, pointer=nil
var s []int            // nil slice

// make: allocate backing array
s = make([]int, 5)     // len=5, cap=5
s = make([]int, 0, 10) // len=0, cap=10 — pre-allocated

// Literal
s := []int{1, 2, 3, 4, 5}

// Slice expressions
s[1:3]   // [2 3]  — from index 1 to 3 (exclusive)
s[:3]    // [1 2 3]
s[2:]    // [3 4 5]
s[:]     // full slice

// append — may allocate new backing array
s = append(s, 6)
s = append(s, 7, 8, 9)
s = append(s, other...)  // append another slice

// copy
dst := make([]int, len(src))
n := copy(dst, src)      // returns number of elements copied

// 2D slice
matrix := make([][]int, rows)
for i := range matrix {
    matrix[i] = make([]int, cols)
}

// Delete element at index i (order preserved)
s = append(s[:i], s[i+1:]...)

// Delete element at index i (order NOT preserved — O(1))
s[i] = s[len(s)-1]
s = s[:len(s)-1]

// Slice internals — sharing backing array
a := []int{1, 2, 3, 4, 5}
b := a[1:3]     // b = [2, 3], shares memory with a
b[0] = 99       // ALSO changes a[1]!
// Fix: use copy() or full slice expression with cap limit
b = a[1:3:3]    // three-index slice — limits cap, forces copy on append
```

### 6.3 Maps

```go
// Declaration
var m map[string]int    // nil map — reading OK, writing panics
m = make(map[string]int)

// Literal
m := map[string]int{
    "alice": 90,
    "bob":   85,
}

// Operations
m["carol"] = 95         // set
v := m["alice"]         // get (zero value if key absent)
v, ok := m["dave"]      // ok = false if key not present
delete(m, "bob")        // delete

// Iterate (order is random — intentional in Go)
for k, v := range m {
    fmt.Printf("%s: %d\n", k, v)
}

// Check existence before use
if count, ok := m[key]; ok {
    fmt.Println(count)
}

// Map of slices — common pattern
graph := make(map[string][]string)
graph["a"] = append(graph["a"], "b")

// Set using map
set := make(map[string]struct{})
set["item"] = struct{}{}
_, exists := set["item"]
```

---

## 7. Structs & Methods

### 7.1 Struct Basics

```go
type Person struct {
    FirstName string
    LastName  string
    Age       int
    email     string  // unexported — lowercase
}

// Initialization
p1 := Person{FirstName: "Alice", LastName: "Smith", Age: 30}
p2 := Person{"Bob", "Jones", 25, "bob@x.com"}   // positional (fragile)
p3 := new(Person)                                 // *Person, zero values
p4 := &Person{FirstName: "Carol"}                 // *Person

// Accessing fields
fmt.Println(p1.FirstName)
p3.Age = 30   // Go auto-dereferences pointers

// Anonymous struct
config := struct {
    Host string
    Port int
}{"localhost", 8080}
```

### 7.2 Embedding (Composition over Inheritance)

```go
type Animal struct {
    Name string
}

func (a Animal) Speak() string {
    return a.Name + " speaks"
}

type Dog struct {
    Animal              // embedded — Dog "inherits" Animal's fields and methods
    Breed string
}

d := Dog{Animal{"Rex"}, "Labrador"}
fmt.Println(d.Name)    // promoted field
fmt.Println(d.Speak()) // promoted method

// Override promoted method
func (d Dog) Speak() string {
    return d.Name + " barks"
}
d.Speak()        // Dog's Speak()
d.Animal.Speak() // Animal's Speak()

// Embedding interfaces — common for decoration
type ReadWriter struct {
    io.Reader
    io.Writer
}
```

### 7.3 Methods

```go
// Value receiver — does NOT modify the original
func (p Person) FullName() string {
    return p.FirstName + " " + p.LastName
}

// Pointer receiver — CAN modify the original
func (p *Person) Birthday() {
    p.Age++
}

// Rule of thumb:
// Use pointer receiver if:
//   - method modifies the receiver
//   - receiver is large (avoid copy)
//   - receiver has a mutex or other non-copyable field
// Be consistent: if ANY method has pointer receiver, prefer ALL to have pointer receiver

// Methods can be called on both pointer and value in most cases
p := Person{FirstName: "Alice", Age: 30}
p.Birthday()   // Go automatically takes &p
(&p).Birthday() // equivalent
```

### 7.4 Struct Tags

```go
type User struct {
    ID       int    `json:"id" db:"user_id"`
    Username string `json:"username" validate:"required,min=3"`
    Password string `json:"-"`                         // omit from JSON
    Email    string `json:"email,omitempty"`           // omit if empty
}

// Read tags with reflection
import "reflect"
t := reflect.TypeOf(User{})
field, _ := t.FieldByName("Username")
fmt.Println(field.Tag.Get("json"))  // "username"
```

---

## 8. Interfaces

### 8.1 Interface Basics

```go
// Interface = set of method signatures
type Animal interface {
    Sound() string
    Move()  string
}

// Implicit satisfaction — no "implements" keyword
type Dog struct{ Name string }

func (d Dog) Sound() string { return "Woof" }
func (d Dog) Move() string  { return "Runs" }

// Dog satisfies Animal automatically
var a Animal = Dog{"Rex"}
fmt.Println(a.Sound())

// Interface with a single method — name it with "-er" suffix (Go convention)
type Reader interface {
    Read(p []byte) (n int, err error)
}
type Writer interface {
    Write(p []byte) (n int, err error)
}
type ReadWriter interface {   // interface composition
    Reader
    Writer
}
```

### 8.2 Empty Interface & Type Assertions

```go
// interface{} (or any in Go 1.18+) — accepts any value
func Print(v interface{}) {
    fmt.Println(v)
}

// Type assertion — extract concrete type
var i interface{} = "hello"
s, ok := i.(string)        // safe assertion
if ok { fmt.Println(s) }

s := i.(string)            // panics if i is not a string — use only when certain

// Type switch
func typeInfo(i interface{}) {
    switch v := i.(type) {
    case int:    fmt.Printf("int: %d\n", v)
    case string: fmt.Printf("string: %s\n", v)
    case []int:  fmt.Printf("[]int len=%d\n", len(v))
    default:     fmt.Printf("unknown: %T\n", v)
    }
}
```

### 8.3 Interface Internals & nil

```go
// An interface value has two components: (type, value)
// nil interface: both type and value are nil
// Non-nil interface with nil value: type is set, value is nil

var err error          // nil interface: type=nil, value=nil
fmt.Println(err == nil) // true

var p *MyError = nil
err = p                // interface: type=*MyError, value=nil
fmt.Println(err == nil) // false — GOTCHA!

// Rule: return error interface, not concrete *MyError, to avoid this
func doWork() error {
    var err *MyError = nil
    return err    // BAD: returns non-nil interface with nil value
}
func doWork() error {
    return nil    // GOOD: returns nil interface
}
```

### 8.4 Common Standard Interfaces

```go
// fmt.Stringer — custom String() for fmt package
type Point struct{ X, Y float64 }
func (p Point) String() string {
    return fmt.Sprintf("(%g, %g)", p.X, p.Y)
}

// error
type ValidationError struct {
    Field   string
    Message string
}
func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation error on %s: %s", e.Field, e.Message)
}

// io.Reader, io.Writer, io.Closer — composable I/O
// sort.Interface
type ByAge []Person
func (a ByAge) Len() int           { return len(a) }
func (a ByAge) Less(i, j int) bool { return a[i].Age < a[j].Age }
func (a ByAge) Swap(i, j int)      { a[i], a[j] = a[j], a[i] }
sort.Sort(ByAge(people))
```

---

## 9. Error Handling

### 9.1 The Error Type

```go
// error is a built-in interface
type error interface {
    Error() string
}

// Creating errors
err1 := errors.New("something went wrong")
err2 := fmt.Errorf("failed to open %s: %w", filename, err)  // wrapping with %w

// Checking errors
if err != nil {
    return fmt.Errorf("context: %w", err)
}

// Sentinel errors — predefined errors to compare against
var ErrNotFound = errors.New("not found")
var ErrPermission = errors.New("permission denied")

if errors.Is(err, ErrNotFound) {
    // handle not found
}
```

### 9.2 Error Wrapping & Unwrapping

```go
// Wrap error with context
err := fmt.Errorf("service.GetUser: %w", ErrNotFound)

// errors.Is — checks entire chain
errors.Is(err, ErrNotFound)   // true, even if wrapped

// errors.As — extracts concrete type from chain
var ve *ValidationError
if errors.As(err, &ve) {
    fmt.Println("field:", ve.Field)
}

// Custom error with extra fields
type DBError struct {
    Code    int
    Message string
    Err     error
}

func (e *DBError) Error() string {
    return fmt.Sprintf("DB error %d: %s", e.Code, e.Message)
}

func (e *DBError) Unwrap() error {
    return e.Err   // enables errors.Is/As to traverse chain
}
```

### 9.3 Error Handling Patterns

```go
// Pattern 1: Early return
func processFile(path string) error {
    f, err := os.Open(path)
    if err != nil {
        return fmt.Errorf("processFile: %w", err)
    }
    defer f.Close()

    data, err := io.ReadAll(f)
    if err != nil {
        return fmt.Errorf("processFile read: %w", err)
    }

    return process(data)
}

// Pattern 2: Errorf helper to reduce if err != nil repetition
type errWriter struct {
    w   io.Writer
    err error
}

func (ew *errWriter) write(buf []byte) {
    if ew.err != nil { return }
    _, ew.err = ew.w.Write(buf)
}

// Pattern 3: Must — panic on error (for init code only)
func MustParse(s string) *template.Template {
    t, err := template.Parse(s)
    if err != nil { panic(err) }
    return t
}
```

---

## 10. Goroutines & Channels

### 10.1 Goroutines

```go
// Start a goroutine — lightweight (starts with ~2KB stack)
go func() {
    fmt.Println("in goroutine")
}()

go doWork()   // existing function

// Goroutines are multiplexed onto OS threads by the Go scheduler (GOMAXPROCS)
runtime.GOMAXPROCS(runtime.NumCPU())  // default since Go 1.5
```

### 10.2 Channels

```go
// Channel — typed conduit for communication between goroutines
ch := make(chan int)           // unbuffered — synchronizes sender & receiver
ch := make(chan int, 10)       // buffered — sender blocks only when full

// Send and receive
ch <- 42        // send (blocks if no receiver or buffer full)
v := <-ch       // receive (blocks until data available)
v, ok := <-ch   // ok=false if channel is closed and empty

// Close a channel — receivers get zero values after all data drained
close(ch)       // only sender should close; closing twice panics

// Range over channel — exits when channel closed
for v := range ch {
    fmt.Println(v)
}

// Directional channels — restrict usage
func producer(ch chan<- int) { ch <- 1 }   // send-only
func consumer(ch <-chan int) { v := <-ch } // receive-only
```

### 10.3 select

```go
// select waits on multiple channel operations — like switch for channels
select {
case msg := <-ch1:
    fmt.Println("received from ch1:", msg)
case msg := <-ch2:
    fmt.Println("received from ch2:", msg)
case ch3 <- "hello":
    fmt.Println("sent to ch3")
default:
    fmt.Println("no channel ready — non-blocking")
}

// Timeout pattern
select {
case res := <-resultCh:
    return res, nil
case <-time.After(5 * time.Second):
    return nil, errors.New("timeout")
}

// Done/cancellation pattern
select {
case work := <-workCh:
    process(work)
case <-ctx.Done():
    return ctx.Err()
}
```

### 10.4 sync Package

```go
import "sync"

// WaitGroup — wait for goroutines to finish
var wg sync.WaitGroup

for _, url := range urls {
    wg.Add(1)
    go func(u string) {
        defer wg.Done()
        fetch(u)
    }(url)
}
wg.Wait()

// Mutex — mutual exclusion
type SafeCounter struct {
    mu    sync.Mutex
    count int
}

func (c *SafeCounter) Inc() {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.count++
}

func (c *SafeCounter) Value() int {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.count
}

// RWMutex — multiple concurrent readers, exclusive writer
type Cache struct {
    mu   sync.RWMutex
    data map[string]string
}

func (c *Cache) Get(key string) (string, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()
    v, ok := c.data[key]
    return v, ok
}

func (c *Cache) Set(key, value string) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.data[key] = value
}

// Once — run exactly once (e.g., singleton init)
var instance *Config
var once sync.Once

func GetConfig() *Config {
    once.Do(func() {
        instance = &Config{} // load from file/env
    })
    return instance
}

// sync.Map — concurrent map (use when many goroutines read/write different keys)
var m sync.Map
m.Store("key", "value")
v, ok := m.Load("key")
m.LoadOrStore("key", "default")
m.Delete("key")
m.Range(func(k, v interface{}) bool {
    fmt.Println(k, v)
    return true // continue iteration
})
```

---

## 11. Concurrency Patterns

### 11.1 Pipeline

```go
// Stage 1: generate
func generate(nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        for _, n := range nums { out <- n }
        close(out)
    }()
    return out
}

// Stage 2: square
func square(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        for n := range in { out <- n * n }
        close(out)
    }()
    return out
}

// Usage
for v := range square(square(generate(1, 2, 3, 4))) {
    fmt.Println(v) // 1, 16, 81, 256
}
```

### 11.2 Fan-Out / Fan-In

```go
// Fan-out: distribute work to multiple goroutines
func fanOut(in <-chan int, numWorkers int) []<-chan int {
    channels := make([]<-chan int, numWorkers)
    for i := 0; i < numWorkers; i++ {
        channels[i] = worker(in)
    }
    return channels
}

// Fan-in: merge multiple channels into one
func merge(channels ...<-chan int) <-chan int {
    var wg sync.WaitGroup
    merged := make(chan int)

    output := func(c <-chan int) {
        defer wg.Done()
        for v := range c { merged <- v }
    }

    wg.Add(len(channels))
    for _, c := range channels {
        go output(c)
    }

    go func() {
        wg.Wait()
        close(merged)
    }()
    return merged
}
```

### 11.3 Worker Pool

```go
func workerPool(jobs <-chan Job, numWorkers int) <-chan Result {
    results := make(chan Result)
    var wg sync.WaitGroup

    for i := 0; i < numWorkers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for job := range jobs {
                results <- process(job)
            }
        }()
    }

    go func() {
        wg.Wait()
        close(results)
    }()
    return results
}

// Usage
jobs := make(chan Job, 100)
results := workerPool(jobs, 5)

for _, j := range allJobs { jobs <- j }
close(jobs)

for r := range results { handle(r) }
```

### 11.4 Context — Cancellation, Timeouts, Deadlines

```go
import "context"

// Root contexts
ctx := context.Background()    // top-level, never cancelled
ctx := context.TODO()          // placeholder during refactoring

// Derived contexts
ctx, cancel := context.WithCancel(parent)
defer cancel()                  // always cancel to release resources

ctx, cancel := context.WithTimeout(parent, 5*time.Second)
defer cancel()

ctx, cancel := context.WithDeadline(parent, time.Now().Add(5*time.Second))
defer cancel()

// Values in context (use sparingly — for request-scoped data only)
type keyType string
const userKey keyType = "user"
ctx = context.WithValue(ctx, userKey, user)
u := ctx.Value(userKey).(*User)

// Checking cancellation
func doWork(ctx context.Context) error {
    for {
        select {
        case <-ctx.Done():
            return ctx.Err()  // context.Canceled or context.DeadlineExceeded
        default:
            // do one unit of work
        }
    }
}

// Pass context as first argument — convention in Go
func fetchUser(ctx context.Context, id int) (*User, error) {
    req, _ := http.NewRequestWithContext(ctx, "GET",
        fmt.Sprintf("/users/%d", id), nil)
    // ...
}
```

### 11.5 Atomic Operations

```go
import "sync/atomic"

var counter int64

// Atomic increment
atomic.AddInt64(&counter, 1)

// Atomic load/store
val := atomic.LoadInt64(&counter)
atomic.StoreInt64(&counter, 100)

// Compare-and-swap
swapped := atomic.CompareAndSwapInt64(&counter, old, new)
```

---

## 12. Generics (Go 1.18+)

### 12.1 Type Parameters

```go
// Generic function
func Map[T, U any](s []T, f func(T) U) []U {
    result := make([]U, len(s))
    for i, v := range s {
        result[i] = f(v)
    }
    return result
}

doubled := Map([]int{1, 2, 3}, func(n int) int { return n * 2 })
lengths := Map([]string{"a", "bb", "ccc"}, func(s string) int { return len(s) })

// Generic struct
type Stack[T any] struct {
    items []T
}

func (s *Stack[T]) Push(v T)          { s.items = append(s.items, v) }
func (s *Stack[T]) Pop() (T, bool) {
    var zero T
    if len(s.items) == 0 { return zero, false }
    v := s.items[len(s.items)-1]
    s.items = s.items[:len(s.items)-1]
    return v, true
}

s := Stack[int]{}
s.Push(1); s.Push(2)
v, _ := s.Pop() // 2
```

### 12.2 Constraints

```go
import "golang.org/x/exp/constraints"

// Built-in constraints
func Min[T constraints.Ordered](a, b T) T {
    if a < b { return a }
    return b
}

Min(3, 5)         // works for int, float64, string, etc.

// Custom constraint
type Number interface {
    ~int | ~int64 | ~float64
}

func Sum[T Number](nums []T) T {
    var total T
    for _, n := range nums { total += n }
    return total
}

// Union constraint
type Stringish interface {
    ~string | ~[]byte
}
```

### 12.3 Common Generic Utilities

```go
// Filter
func Filter[T any](s []T, pred func(T) bool) []T {
    var result []T
    for _, v := range s {
        if pred(v) { result = append(result, v) }
    }
    return result
}

// Reduce
func Reduce[T, U any](s []T, init U, f func(U, T) U) U {
    result := init
    for _, v := range s { result = f(result, v) }
    return result
}

// Contains
func Contains[T comparable](s []T, target T) bool {
    for _, v := range s {
        if v == target { return true }
    }
    return false
}

// Keys and Values from map
func Keys[K comparable, V any](m map[K]V) []K {
    keys := make([]K, 0, len(m))
    for k := range m { keys = append(keys, k) }
    return keys
}
```

---

## 13. Packages, Modules & Project Structure

### 13.1 Modules

```bash
# Initialize a module
go mod init github.com/username/myproject

# Add dependency
go get github.com/gin-gonic/gin@v1.9.1

# Tidy (remove unused, add missing)
go mod tidy

# Vendor dependencies (for reproducible builds)
go mod vendor

# go.mod structure
module github.com/username/myproject
go 1.21

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/jmoiron/sqlx v1.3.5
)
```

### 13.2 Package Conventions

```go
// Package declaration — matches directory name
package user

// Exported = capitalized
func GetUser() {}    // visible outside package
type User struct{}   // visible outside package

// Unexported = lowercase
func validate() {}   // only within package
type cache struct{}  // only within package

// Package-level init — runs once when package is imported
func init() {
    // register drivers, init globals, etc.
}

// Blank import — import for side effects only
import _ "github.com/lib/pq"  // registers PostgreSQL driver
```

### 13.3 Project Structure (Standard Layout)

```
myproject/
├── cmd/
│   └── api/
│       └── main.go          ← entry points
├── internal/                 ← private packages (not importable outside)
│   ├── user/
│   │   ├── handler.go
│   │   ├── service.go
│   │   ├── repository.go
│   │   └── model.go
│   ├── order/
│   └── middleware/
├── pkg/                      ← public reusable packages
│   ├── logger/
│   └── validator/
├── api/                      ← API definitions (OpenAPI/proto)
├── config/
├── migrations/
├── scripts/
├── go.mod
├── go.sum
└── Makefile
```

### 13.4 Dependency Injection Pattern

```go
// Instead of global state or singletons, pass dependencies explicitly

type UserRepository interface {
    GetByID(ctx context.Context, id int) (*User, error)
    Save(ctx context.Context, user *User) error
}

type UserService struct {
    repo   UserRepository
    logger *slog.Logger
    cache  Cache
}

func NewUserService(repo UserRepository, logger *slog.Logger, cache Cache) *UserService {
    return &UserService{repo: repo, logger: logger, cache: cache}
}

// Wire everything up in main.go
func main() {
    db := connectDB()
    repo := postgres.NewUserRepository(db)
    cache := redis.NewCache()
    logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))
    svc := user.NewUserService(repo, logger, cache)
    handler := http.NewUserHandler(svc)
    // ...
}
```

---

## 14. Standard Library Essentials

### 14.1 fmt

```go
// Print
fmt.Print("no newline")
fmt.Println("with newline")
fmt.Printf("formatted: %d %s %v\n", 42, "hello", struct{ X int }{1})

// Sprint — return string
s := fmt.Sprintf("user: %s, age: %d", name, age)

// Verbs
%v   // default format
%+v  // struct with field names
%#v  // Go syntax representation
%T   // type
%d   // integer (decimal)
%b   // binary
%x   // hex (lowercase)
%f   // float
%e   // scientific notation
%s   // string
%q   // quoted string
%p   // pointer address
%t   // boolean

// Scan
var n int
fmt.Scan(&n)
fmt.Scanf("%d", &n)
```

### 14.2 strings & strconv

```go
import "strings"

strings.Contains("seafood", "foo")       // true
strings.HasPrefix("seafood", "sea")      // true
strings.HasSuffix("seafood", "food")     // true
strings.Index("seafood", "foo")          // 3
strings.Count("cheese", "e")             // 3
strings.Replace("oink oink oink", "oink", "moo", 2)  // "moo moo oink"
strings.ReplaceAll("oink oink", "oink", "moo")
strings.ToUpper("hello")                 // "HELLO"
strings.ToLower("HELLO")                 // "hello"
strings.TrimSpace("  hello  ")           // "hello"
strings.Trim("  hello  ", " ")           // "hello"
strings.TrimLeft("¡¡¡hello!!!", "!¡")
strings.Split("a,b,c", ",")             // ["a" "b" "c"]
strings.Join([]string{"a","b"}, "-")    // "a-b"
strings.Fields("  foo bar baz  ")       // ["foo" "bar" "baz"]
strings.Repeat("ab", 3)                 // "ababab"
strings.EqualFold("Go", "go")           // true (case-insensitive)

// strings.Builder for efficient concatenation
var b strings.Builder
for i := 0; i < 5; i++ {
    fmt.Fprintf(&b, "%d", i)
}
fmt.Println(b.String()) // "01234"

// strings.Reader implements io.Reader
r := strings.NewReader("hello")

import "strconv"
strconv.Itoa(42)           // "42"
strconv.Atoi("42")         // 42, nil
strconv.ParseBool("true")  // true, nil
strconv.FormatFloat(3.14, 'f', 2, 64)  // "3.14"
strconv.ParseFloat("3.14", 64)         // 3.14, nil
```

### 14.3 time

```go
import "time"

now := time.Now()
t := time.Date(2024, time.January, 15, 10, 30, 0, 0, time.UTC)

// Duration
d := 5 * time.Second
d := 2*time.Hour + 30*time.Minute

// Formatting (reference time: Mon Jan 2 15:04:05 MST 2006)
t.Format("2006-01-02 15:04:05")
t.Format(time.RFC3339)
t.Format("02/01/2006")

// Parsing
t, err := time.Parse("2006-01-02", "2024-01-15")
t, err := time.Parse(time.RFC3339, "2024-01-15T10:30:00Z")

// Operations
t.Add(24 * time.Hour)
t.Sub(other)         // Duration
t.Before(other)
t.After(other)
t.Equal(other)

// Timer / Ticker
timer := time.NewTimer(5 * time.Second)
<-timer.C            // blocks until timer fires
timer.Stop()

ticker := time.NewTicker(1 * time.Second)
for t := range ticker.C {
    fmt.Println(t)
}
ticker.Stop()

// Sleep
time.Sleep(100 * time.Millisecond)
```

### 14.4 os & io

```go
import "os"
import "io"
import "bufio"

// Environment
os.Getenv("HOME")
os.Setenv("KEY", "value")

// File operations
f, err := os.Open("file.txt")           // read-only
f, err := os.Create("file.txt")         // write, truncate
f, err := os.OpenFile("file.txt", os.O_APPEND|os.O_WRONLY, 0644)
defer f.Close()

// Read
data, err := os.ReadFile("file.txt")    // entire file into []byte
io.ReadAll(reader)                       // read all from any Reader

// Write
os.WriteFile("file.txt", data, 0644)
fmt.Fprintln(f, "line")

// Buffered I/O
reader := bufio.NewReader(f)
line, err := reader.ReadString('\n')

scanner := bufio.NewScanner(f)
for scanner.Scan() {
    fmt.Println(scanner.Text())
}

writer := bufio.NewWriter(f)
writer.WriteString("hello\n")
writer.Flush()

// Directory
os.Mkdir("dir", 0755)
os.MkdirAll("a/b/c", 0755)
os.Remove("file.txt")
os.RemoveAll("dir")
entries, _ := os.ReadDir(".")
for _, e := range entries {
    fmt.Println(e.Name(), e.IsDir())
}

// Args, Exit
os.Args   // []string — program args
os.Exit(1)
os.Stdin, os.Stdout, os.Stderr  // standard streams
```

### 14.5 encoding/json

```go
import "encoding/json"

type User struct {
    ID    int    `json:"id"`
    Name  string `json:"name"`
    Email string `json:"email,omitempty"`
}

// Marshal — struct → JSON
data, err := json.Marshal(user)
data, err := json.MarshalIndent(user, "", "  ")  // pretty print

// Unmarshal — JSON → struct
var u User
err := json.Unmarshal(data, &u)

// Streaming (large data)
encoder := json.NewEncoder(w)
encoder.Encode(user)

decoder := json.NewDecoder(r)
decoder.Decode(&user)

// Dynamic JSON
var m map[string]interface{}
json.Unmarshal(data, &m)

// Raw message (defer parsing)
type Response struct {
    Status string          `json:"status"`
    Data   json.RawMessage `json:"data"`
}
```

### 14.6 sort

```go
import "sort"

// Primitive slices
sort.Ints([]int{3, 1, 2})
sort.Strings([]string{"c", "a", "b"})
sort.Float64s([]float64{3.0, 1.5, 2.0})

// Reverse
sort.Sort(sort.Reverse(sort.IntSlice(nums)))

// Custom sort with sort.Slice (no interface needed)
people := []Person{{Name: "Bob", Age: 25}, {Name: "Alice", Age: 30}}
sort.Slice(people, func(i, j int) bool {
    return people[i].Age < people[j].Age
})

// Stable sort (preserves order of equal elements)
sort.SliceStable(people, func(i, j int) bool {
    return people[i].Name < people[j].Name
})

// Binary search
idx := sort.SearchInts(sorted, target)   // returns insertion point
found := idx < len(sorted) && sorted[idx] == target
```

### 14.7 math & math/rand

```go
import "math"
import "math/rand/v2"

math.Abs(-3.5)          // 3.5
math.Max(3.0, 5.0)      // 5.0
math.Min(3.0, 5.0)      // 3.0
math.Sqrt(16.0)         // 4.0
math.Pow(2, 10)         // 1024
math.Log(math.E)        // 1.0
math.Log2(8)            // 3.0
math.Floor(3.7)         // 3.0
math.Ceil(3.2)          // 4.0
math.Round(3.5)         // 4.0
math.MaxInt64           // max int64
math.Pi                 // 3.141592...

// Random (crypto-seeded by default in v2)
n := rand.IntN(100)             // [0, 100)
f := rand.Float64()             // [0.0, 1.0)
rand.Shuffle(len(s), func(i, j int) { s[i], s[j] = s[j], s[i] })
```

---

## 15. HTTP Servers & REST APIs

### 15.1 net/http — Standard Library

```go
import "net/http"

// Handler interface
type Handler interface {
    ServeHTTP(ResponseWriter, *Request)
}

// HandlerFunc adapts a function to Handler
func hello(w http.ResponseWriter, r *http.Request) {
    fmt.Fprintf(w, "Hello, World!")
}

// ServeMux (router)
mux := http.NewServeMux()
mux.HandleFunc("GET /users", listUsers)
mux.HandleFunc("POST /users", createUser)
mux.HandleFunc("GET /users/{id}", getUser)   // Go 1.22 path params

// Server
srv := &http.Server{
    Addr:         ":8080",
    Handler:      mux,
    ReadTimeout:  10 * time.Second,
    WriteTimeout: 10 * time.Second,
    IdleTimeout:  60 * time.Second,
}
if err := srv.ListenAndServe(); err != nil {
    log.Fatal(err)
}

// Handler with context
func getUser(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    id := r.PathValue("id")          // Go 1.22+
    user, err := svc.GetUser(ctx, id)
    if err != nil {
        http.Error(w, "not found", http.StatusNotFound)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(user)
}
```

### 15.2 Middleware Pattern

```go
type Middleware func(http.Handler) http.Handler

// Logging middleware
func Logger(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        next.ServeHTTP(w, r)
        log.Printf("%s %s %v", r.Method, r.URL.Path, time.Since(start))
    })
}

// Auth middleware
func Auth(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        token := r.Header.Get("Authorization")
        if !validateToken(token) {
            http.Error(w, "unauthorized", http.StatusUnauthorized)
            return
        }
        next.ServeHTTP(w, r)
    })
}

// Chaining middleware
func Chain(h http.Handler, middlewares ...Middleware) http.Handler {
    for i := len(middlewares) - 1; i >= 0; i-- {
        h = middlewares[i](h)
    }
    return h
}

handler := Chain(mux, Logger, Auth, RateLimit)
```

### 15.3 ResponseWriter Wrapper (for status code logging)

```go
type responseWriter struct {
    http.ResponseWriter
    status int
    size   int
}

func (rw *responseWriter) WriteHeader(status int) {
    rw.status = status
    rw.ResponseWriter.WriteHeader(status)
}

func (rw *responseWriter) Write(b []byte) (int, error) {
    n, err := rw.ResponseWriter.Write(b)
    rw.size += n
    return n, err
}
```

### 15.4 Graceful Shutdown

```go
func main() {
    srv := &http.Server{Addr: ":8080", Handler: mux}

    go func() {
        if err := srv.ListenAndServe(); err != http.ErrServerClosed {
            log.Fatal(err)
        }
    }()

    quit := make(chan os.Signal, 1)
    signal.Notify(quit, os.Interrupt, syscall.SIGTERM)
    <-quit

    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()
    if err := srv.Shutdown(ctx); err != nil {
        log.Fatal("Shutdown error:", err)
    }
    log.Println("Server stopped")
}
```

### 15.5 HTTP Client

```go
client := &http.Client{
    Timeout: 10 * time.Second,
    Transport: &http.Transport{
        MaxIdleConns:        100,
        MaxIdleConnsPerHost: 10,
        IdleConnTimeout:     90 * time.Second,
    },
}

// GET
req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
req.Header.Set("Authorization", "Bearer "+token)
resp, err := client.Do(req)
defer resp.Body.Close()
body, err := io.ReadAll(resp.Body)

// POST JSON
data, _ := json.Marshal(payload)
req, _ := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(data))
req.Header.Set("Content-Type", "application/json")
resp, err := client.Do(req)
```

---

## 16. Database Patterns

### 16.1 database/sql

```go
import (
    "database/sql"
    _ "github.com/lib/pq"  // PostgreSQL driver
)

db, err := sql.Open("postgres", "postgres://user:pass@localhost/dbname?sslmode=disable")
if err != nil { log.Fatal(err) }

// Connection pool settings
db.SetMaxOpenConns(25)
db.SetMaxIdleConns(25)
db.SetConnMaxLifetime(5 * time.Minute)

// Query one row
var u User
err = db.QueryRowContext(ctx,
    "SELECT id, name, email FROM users WHERE id = $1", id).
    Scan(&u.ID, &u.Name, &u.Email)
if err == sql.ErrNoRows { return nil, ErrNotFound }

// Query multiple rows
rows, err := db.QueryContext(ctx, "SELECT id, name FROM users WHERE active = $1", true)
defer rows.Close()
var users []User
for rows.Next() {
    var u User
    if err := rows.Scan(&u.ID, &u.Name); err != nil { return nil, err }
    users = append(users, u)
}
if err := rows.Err(); err != nil { return nil, err }

// Exec (INSERT/UPDATE/DELETE)
result, err := db.ExecContext(ctx,
    "INSERT INTO users (name, email) VALUES ($1, $2)", name, email)
lastID, _ := result.LastInsertId()
rowsAffected, _ := result.RowsAffected()

// Prepared statements (reuse across multiple calls)
stmt, err := db.PrepareContext(ctx, "SELECT * FROM users WHERE id = $1")
defer stmt.Close()
row := stmt.QueryRowContext(ctx, id)

// Transactions
tx, err := db.BeginTx(ctx, nil)
if err != nil { return err }
defer func() {
    if p := recover(); p != nil {
        tx.Rollback()
        panic(p)
    } else if err != nil {
        tx.Rollback()
    } else {
        err = tx.Commit()
    }
}()
_, err = tx.ExecContext(ctx, "UPDATE accounts SET balance = balance - $1 WHERE id = $2", amount, fromID)
if err != nil { return err }
_, err = tx.ExecContext(ctx, "UPDATE accounts SET balance = balance + $1 WHERE id = $2", amount, toID)
```

### 16.2 Repository Pattern

```go
type UserRepository interface {
    GetByID(ctx context.Context, id int) (*User, error)
    GetByEmail(ctx context.Context, email string) (*User, error)
    List(ctx context.Context, filter UserFilter) ([]*User, error)
    Create(ctx context.Context, user *User) error
    Update(ctx context.Context, user *User) error
    Delete(ctx context.Context, id int) error
}

type postgresUserRepo struct {
    db *sql.DB
}

func NewUserRepository(db *sql.DB) UserRepository {
    return &postgresUserRepo{db: db}
}

func (r *postgresUserRepo) GetByID(ctx context.Context, id int) (*User, error) {
    q := `SELECT id, name, email, created_at FROM users WHERE id = $1`
    var u User
    err := r.db.QueryRowContext(ctx, q, id).
        Scan(&u.ID, &u.Name, &u.Email, &u.CreatedAt)
    if err == sql.ErrNoRows { return nil, ErrNotFound }
    if err != nil { return nil, fmt.Errorf("GetByID: %w", err) }
    return &u, nil
}
```

---

## 17. Testing

### 17.1 Unit Tests

```go
// user_test.go — same package (white box) or user_test (black box)
package user_test

import (
    "testing"
    "github.com/myapp/user"
)

func TestAdd(t *testing.T) {
    got := user.Add(2, 3)
    want := 5
    if got != want {
        t.Errorf("Add(2,3) = %d, want %d", got, want)
    }
}

// Table-driven tests — idiomatic Go
func TestDivide(t *testing.T) {
    tests := []struct {
        name    string
        a, b    float64
        want    float64
        wantErr bool
    }{
        {"positive", 10, 2, 5.0, false},
        {"negative divisor", 10, -2, -5.0, false},
        {"zero divisor", 10, 0, 0, true},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := user.Divide(tt.a, tt.b)
            if (err != nil) != tt.wantErr {
                t.Errorf("Divide() error = %v, wantErr %v", err, tt.wantErr)
                return
            }
            if got != tt.want {
                t.Errorf("Divide() = %v, want %v", got, tt.want)
            }
        })
    }
}

// Test helpers
func assertEqual[T comparable](t *testing.T, got, want T) {
    t.Helper()
    if got != want {
        t.Errorf("got %v, want %v", got, want)
    }
}
```

### 17.2 Test Setup & Teardown

```go
func TestMain(m *testing.M) {
    // Setup before all tests in the package
    db = setupTestDB()

    code := m.Run()  // run all tests

    // Teardown
    db.Close()
    os.Exit(code)
}

// Per-test setup with t.Cleanup
func TestSomething(t *testing.T) {
    db := setupDB(t)
    t.Cleanup(func() { db.Close() })  // runs after test (even on failure)
    // ...
}
```

### 17.3 Mocking with Interfaces

```go
// Define interface
type UserRepo interface {
    GetByID(ctx context.Context, id int) (*User, error)
}

// Mock implementation
type mockUserRepo struct {
    users map[int]*User
    err   error
}

func (m *mockUserRepo) GetByID(ctx context.Context, id int) (*User, error) {
    if m.err != nil { return nil, m.err }
    u, ok := m.users[id]
    if !ok { return nil, ErrNotFound }
    return u, nil
}

// Test using mock
func TestGetUser(t *testing.T) {
    repo := &mockUserRepo{
        users: map[int]*User{1: {ID: 1, Name: "Alice"}},
    }
    svc := NewUserService(repo)
    u, err := svc.GetUser(context.Background(), 1)
    // assertions...
}
```

### 17.4 Benchmarks

```go
func BenchmarkFibonacci(b *testing.B) {
    for i := 0; i < b.N; i++ {
        Fibonacci(20)
    }
}

// Sub-benchmarks
func BenchmarkSort(b *testing.B) {
    sizes := []int{100, 1000, 10000}
    for _, n := range sizes {
        b.Run(fmt.Sprintf("size-%d", n), func(b *testing.B) {
            data := generateData(n)
            b.ResetTimer()
            for i := 0; i < b.N; i++ {
                sort.Ints(data)
            }
        })
    }
}
```

```bash
go test ./...                    # run all tests
go test -v ./...                 # verbose
go test -run TestAdd             # specific test
go test -run TestDivide/zero     # specific subtest
go test -bench=.                 # run benchmarks
go test -bench=. -benchmem       # with memory allocation stats
go test -cover                   # coverage
go test -coverprofile=out.cov && go tool cover -html=out.cov
go test -race ./...              # race detector
```

---

## 18. Common Go Patterns

### 18.1 Functional Options

```go
// Clean API for configuring structs with many optional fields
type Server struct {
    host    string
    port    int
    timeout time.Duration
    maxConn int
}

type Option func(*Server)

func WithHost(host string) Option {
    return func(s *Server) { s.host = host }
}

func WithPort(port int) Option {
    return func(s *Server) { s.port = port }
}

func WithTimeout(d time.Duration) Option {
    return func(s *Server) { s.timeout = d }
}

func NewServer(opts ...Option) *Server {
    s := &Server{
        host:    "localhost",     // defaults
        port:    8080,
        timeout: 30 * time.Second,
        maxConn: 100,
    }
    for _, opt := range opts { opt(s) }
    return s
}

// Usage
srv := NewServer(
    WithHost("0.0.0.0"),
    WithPort(9090),
    WithTimeout(60*time.Second),
)
```

### 18.2 Result Type (Wrapping error + value)

```go
type Result[T any] struct {
    value T
    err   error
}

func Ok[T any](v T) Result[T]    { return Result[T]{value: v} }
func Err[T any](e error) Result[T] { return Result[T]{err: e} }

func (r Result[T]) Unwrap() (T, error) { return r.value, r.err }

func (r Result[T]) Must() T {
    if r.err != nil { panic(r.err) }
    return r.value
}
```

### 18.3 Retry Pattern

```go
func Retry(ctx context.Context, maxAttempts int,
    delay time.Duration, fn func() error) error {
    var err error
    for attempt := 0; attempt < maxAttempts; attempt++ {
        if err = fn(); err == nil {
            return nil
        }
        select {
        case <-ctx.Done():
            return ctx.Err()
        case <-time.After(delay * time.Duration(1<<attempt)):  // exponential backoff
        }
    }
    return fmt.Errorf("after %d attempts: %w", maxAttempts, err)
}

// Usage
err := Retry(ctx, 3, time.Second, func() error {
    return callExternalAPI()
})
```

### 18.4 Circuit Breaker

```go
type CircuitBreaker struct {
    mu           sync.Mutex
    state        string  // "closed", "open", "half-open"
    failures     int
    maxFailures  int
    lastAttempt  time.Time
    timeout      time.Duration
}

func (cb *CircuitBreaker) Execute(fn func() error) error {
    cb.mu.Lock()
    defer cb.mu.Unlock()

    switch cb.state {
    case "open":
        if time.Since(cb.lastAttempt) > cb.timeout {
            cb.state = "half-open"
        } else {
            return errors.New("circuit breaker open")
        }
    }

    err := fn()
    if err != nil {
        cb.failures++
        cb.lastAttempt = time.Now()
        if cb.failures >= cb.maxFailures {
            cb.state = "open"
        }
        return err
    }
    cb.failures = 0
    cb.state = "closed"
    return nil
}
```

### 18.5 Object Pool

```go
import "sync"

var bufPool = sync.Pool{
    New: func() interface{} {
        return make([]byte, 0, 1024)
    },
}

func processRequest(data []byte) {
    buf := bufPool.Get().([]byte)
    defer func() {
        buf = buf[:0]        // reset length, keep capacity
        bufPool.Put(buf)
    }()

    buf = append(buf, data...)
    // use buf
}
```

### 18.6 Event Bus

```go
type EventBus struct {
    mu          sync.RWMutex
    subscribers map[string][]func(interface{})
}

func NewEventBus() *EventBus {
    return &EventBus{subscribers: make(map[string][]func(interface{}))}
}

func (eb *EventBus) Subscribe(event string, handler func(interface{})) {
    eb.mu.Lock()
    defer eb.mu.Unlock()
    eb.subscribers[event] = append(eb.subscribers[event], handler)
}

func (eb *EventBus) Publish(event string, data interface{}) {
    eb.mu.RLock()
    handlers := eb.subscribers[event]
    eb.mu.RUnlock()

    for _, h := range handlers {
        go h(data)   // async delivery
    }
}
```

### 18.7 Iterator Pattern (Go 1.23+ range-over-func)

```go
// Pre-1.23: closure iterator
func Fibonacci() func() int {
    a, b := 0, 1
    return func() int {
        v := a
        a, b = b, a+b
        return v
    }
}

next := Fibonacci()
for i := 0; i < 10; i++ {
    fmt.Println(next())
}

// Go 1.23+ iter package
func Fib(yield func(int) bool) {
    a, b := 0, 1
    for yield(a) {
        a, b = b, a+b
    }
}

for n := range Fib {
    if n > 100 { break }
    fmt.Println(n)
}
```

---

## 19. Performance & Memory

### 19.1 Common Performance Tips

```go
// 1. Pre-allocate slices when size is known
result := make([]int, 0, len(input))  // avoids repeated reallocation

// 2. Use strings.Builder for string concatenation in loops
var b strings.Builder
for _, s := range parts { b.WriteString(s) }
result := b.String()

// 3. Avoid interface{} boxing in hot paths — use concrete types or generics

// 4. Reuse buffers with sync.Pool

// 5. Use buffered channels to decouple producers and consumers

// 6. Avoid unnecessary allocations — prefer stack allocation
func sum(nums []int) int {  // nums passed as slice header (24 bytes), no heap alloc
    total := 0
    for _, n := range nums { total += n }
    return total
}

// 7. Use strconv over fmt for numeric conversions in hot paths
strconv.Itoa(n)    // faster than fmt.Sprintf("%d", n)

// 8. Profile before optimizing
```

### 19.2 Profiling

```bash
# CPU profile
go test -cpuprofile=cpu.out -bench=.
go tool pprof cpu.out

# Memory profile
go test -memprofile=mem.out -bench=.
go tool pprof mem.out

# In-process profiling
import _ "net/http/pprof"

go func() {
    log.Println(http.ListenAndServe("localhost:6060", nil))
}()

# Then: go tool pprof http://localhost:6060/debug/pprof/profile
```

### 19.3 Memory Model Highlights

```go
// Goroutine stack starts at 2KB, grows as needed (up to 1GB default)
// Heap-allocated: objects that escape to heap (escape analysis)
// Stack-allocated: local variables that don't escape (faster, no GC)

// To check escape analysis:
// go build -gcflags="-m" ./...

// GC tuning
import "runtime/debug"
debug.SetGCPercent(200)        // GC when heap grows 200% (default 100%)
debug.SetMemoryLimit(500 << 20) // GOMEMLIMIT in Go 1.19+
```

### 19.4 Race Detector

```go
// Always run tests with -race in CI
// go test -race ./...

// Common races:
// 1. Concurrent map read/write — use sync.Map or mutex
// 2. Closure capturing loop variable
// 3. Unsynchronized counter — use sync/atomic or mutex
```

---

## 20. Interview Questions & Answers

### 20.1 Language Fundamentals

**Q: What is the difference between `make` and `new`?**
```
new(T)    — allocates zeroed memory for type T, returns *T
            Works for any type
            Rarely needed in Go

make(T)   — creates and initializes slices, maps, and channels
            Returns T (not *T) — these types need internal initialization
            Only works for slice, map, chan
```

**Q: What happens when you write to a nil map?**
```
Runtime panic: assignment to entry in nil map
Reading from nil map is safe (returns zero value)
Always initialize: m := make(map[K]V) or m := map[K]V{}
```

**Q: Explain goroutine vs OS thread.**
```
OS Thread:   ~2MB stack, scheduled by OS, expensive context switch
Goroutine:   ~2KB stack (grows), scheduled by Go runtime (M:N threading),
             cheap to create (can have millions)
             Go scheduler uses GOMAXPROCS OS threads (default = num CPUs)
```

**Q: What is a channel direction and why use it?**
```go
// Restricts usage at compile time — documents intent, prevents bugs
func produce(ch chan<- int) { ch <- 1 }     // can only send
func consume(ch <-chan int) { v := <-ch }   // can only receive
```

**Q: When does a goroutine leak, and how to fix it?**
```go
// LEAK: goroutine blocked on channel send/receive with no one on other side
func leak() {
    ch := make(chan int)
    go func() { ch <- 1 }()   // blocked forever if no receiver
}

// FIX: use context for cancellation
func noLeak(ctx context.Context) {
    ch := make(chan int, 1)
    go func() {
        select {
        case ch <- 1:
        case <-ctx.Done():
        }
    }()
}
```

**Q: What is the difference between buffered and unbuffered channels?**
```
Unbuffered: send blocks until receiver is ready (synchronization point)
Buffered:   send blocks only when buffer is full (decouples sender/receiver)

Use unbuffered for synchronization guarantees
Use buffered to absorb bursts, improve throughput
```

**Q: What is defer's execution order?**
```go
// LIFO — last deferred runs first
func f() {
    defer fmt.Println("1")   // runs third
    defer fmt.Println("2")   // runs second
    defer fmt.Println("3")   // runs first
}
// Output: 3, 2, 1

// Deferred function arguments evaluated immediately
x := 10
defer fmt.Println(x)  // prints 10, not value at function end
x = 20
```

**Q: How does Go handle circular imports?**
```
Go does NOT allow circular imports — compile error.
Fix by:
  1. Extracting shared types to a third package
  2. Using interfaces to break the dependency
  3. Restructuring package hierarchy
```

**Q: Explain interface nil pitfall.**
```go
var err *MyError = nil
var iface error = err       // iface is NOT nil! has type but nil value
fmt.Println(iface == nil)   // false

// Rule: return concrete nil, not typed nil through interface
func bad() error { var e *MyError; return e }   // BAD
func good() error { return nil }                // GOOD
```

### 20.2 Concurrency Questions

**Q: What is the difference between `sync.Mutex` and `sync.RWMutex`?**
```
Mutex:    one goroutine at a time (read OR write)
RWMutex:  multiple concurrent readers OR one exclusive writer
          Use RWMutex when reads >> writes for better throughput
```

**Q: How to implement a concurrent-safe singleton?**
```go
var (
    instance *Config
    once     sync.Once
)

func GetConfig() *Config {
    once.Do(func() { instance = &Config{} })
    return instance
}
// sync.Once guarantees exactly one execution, even with concurrent callers
```

**Q: What causes a deadlock in Go?**
```
1. Two goroutines waiting for each other's lock
2. Goroutine waiting to receive from channel no one sends to
3. Goroutine waiting to send to channel no one receives from
4. main goroutine exits while others are still running (not deadlock, just exit)

Go runtime detects deadlocks involving ALL goroutines and panics:
"fatal error: all goroutines are asleep - deadlock!"
```

**Q: What is `select` with default?**
```go
// Non-blocking channel operation
select {
case v := <-ch:
    process(v)
default:
    // ch is empty — continue without blocking
}
```

**Q: How to safely share data between goroutines?**
```
Option 1: Channels — "don't communicate by sharing memory; share memory by communicating"
Option 2: sync.Mutex / sync.RWMutex
Option 3: sync/atomic for simple counters/flags
Option 4: sync.Map for concurrent map access
```

### 20.3 Design & Architecture Questions

**Q: How do you implement dependency injection in Go?**
```go
// Interfaces + constructor injection (no framework needed)
type Service struct {
    repo   Repository  // interface, not concrete type
    logger Logger
}

func NewService(repo Repository, logger Logger) *Service {
    return &Service{repo: repo, logger: logger}
}
// In tests: inject mock implementations
// In prod:  inject real implementations
```

**Q: What is the difference between value and pointer receivers?**
```go
// Value receiver — works on a COPY — cannot modify original
func (u User) Name() string { return u.name }

// Pointer receiver — works on the ORIGINAL — can modify
func (u *User) SetName(name string) { u.name = name }

// Rule: if ANY method has pointer receiver, make ALL methods pointer receivers
// Pointer receivers are needed when: modifying state, large structs, non-copyable fields
```

**Q: How do you handle configuration in Go?**
```go
type Config struct {
    DBHost     string
    DBPort     int
    DBName     string
    ServerPort int
    LogLevel   string
}

func LoadConfig() (*Config, error) {
    return &Config{
        DBHost:     getEnv("DB_HOST", "localhost"),
        DBPort:     getEnvInt("DB_PORT", 5432),
        DBName:     mustGetEnv("DB_NAME"),
        ServerPort: getEnvInt("PORT", 8080),
        LogLevel:   getEnv("LOG_LEVEL", "info"),
    }, nil
}

func getEnv(key, fallback string) string {
    if v := os.Getenv(key); v != "" { return v }
    return fallback
}
func mustGetEnv(key string) string {
    v := os.Getenv(key)
    if v == "" { panic(fmt.Sprintf("env var %s is required", key)) }
    return v
}
```

### 20.4 Coding Problems (Common in Go Interviews)

**Implement LRU Cache:**
```go
type LRUCache struct {
    cap   int
    cache map[int]*node
    head  *node  // most recent
    tail  *node  // least recent
}

type node struct {
    key, val   int
    prev, next *node
}

func NewLRUCache(cap int) *LRUCache {
    h, t := &node{}, &node{}
    h.next = t; t.prev = h
    return &LRUCache{cap: cap, cache: make(map[int]*node), head: h, tail: t}
}

func (c *LRUCache) Get(key int) int {
    if n, ok := c.cache[key]; ok {
        c.remove(n); c.insertFront(n)
        return n.val
    }
    return -1
}

func (c *LRUCache) Put(key, val int) {
    if n, ok := c.cache[key]; ok { c.remove(n) }
    n := &node{key: key, val: val}
    c.cache[key] = n
    c.insertFront(n)
    if len(c.cache) > c.cap {
        lru := c.tail.prev
        c.remove(lru)
        delete(c.cache, lru.key)
    }
}

func (c *LRUCache) remove(n *node) {
    n.prev.next = n.next; n.next.prev = n.prev
}

func (c *LRUCache) insertFront(n *node) {
    n.next = c.head.next; n.prev = c.head
    c.head.next.prev = n; c.head.next = n
}
```

**Concurrent map with sharding (reduce lock contention):**
```go
type ShardedMap struct {
    shards [256]struct {
        sync.RWMutex
        m map[string]interface{}
    }
}

func (sm *ShardedMap) shard(key string) int {
    h := fnv.New32a()
    h.Write([]byte(key))
    return int(h.Sum32()) % 256
}

func (sm *ShardedMap) Set(key string, val interface{}) {
    s := sm.shard(key)
    sm.shards[s].Lock()
    defer sm.shards[s].Unlock()
    sm.shards[s].m[key] = val
}

func (sm *ShardedMap) Get(key string) (interface{}, bool) {
    s := sm.shard(key)
    sm.shards[s].RLock()
    defer sm.shards[s].RUnlock()
    v, ok := sm.shards[s].m[key]
    return v, ok
}
```

**Worker pool with context:**
```go
func WorkerPool(ctx context.Context, jobs []Job,
    numWorkers int, process func(Job) Result) []Result {

    jobCh := make(chan Job, len(jobs))
    resCh := make(chan Result, len(jobs))

    var wg sync.WaitGroup
    for i := 0; i < numWorkers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for {
                select {
                case job, ok := <-jobCh:
                    if !ok { return }
                    resCh <- process(job)
                case <-ctx.Done():
                    return
                }
            }
        }()
    }

    for _, j := range jobs { jobCh <- j }
    close(jobCh)

    go func() { wg.Wait(); close(resCh) }()

    var results []Result
    for r := range resCh { results = append(results, r) }
    return results
}
```

### 20.5 Quick Reference — Things That Catch People

```
1. Maps are unordered — never rely on iteration order
2. Slice header copy — slices passed to functions share backing array
3. nil map read = ok, nil map write = panic
4. Goroutine leaks — always provide cancellation via context or done channel
5. Interface nil != typed nil with nil value
6. defer arguments evaluated at defer site, not at execution time
7. Named return + defer can return unexpected values if not careful
8. Closing a channel twice panics — only close once, from sender
9. Sending to a closed channel panics
10. Goroutines are not garbage collected — they must return
11. String is immutable — each modification allocates; use strings.Builder
12. for range on string yields runes (not bytes)
13. go vet catches common mistakes; run before submitting code
14. GOMAXPROCS defaults to num CPUs — Go uses all cores by default
15. copy() only copies min(len(dst), len(src)) elements
```

---

*This file pairs with `DSA_PATTERNS.md`, `CONCEPTS.md`, and `LLD_OOD.md` to form a complete interview preparation suite.*
