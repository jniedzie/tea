//  Collection.hpp
//
//  Created by Jeremi Niedziela on 07/08/2023.

#ifndef Collection_hpp
#define Collection_hpp

#include <vector>
#include <cstddef>
#include <algorithm>

template <typename T>
class Collection : public std::vector<T> {
 private:
 public:
  size_t stopIndex = 0;
  // The event-reported collection size may be larger than the backing vector
  // (for example when an input event exceeds maxCollectionElements).  Never
  // let iteration expose elements that do not exist.
  void ChangeVisibleSize(size_t index) { stopIndex = std::min(index, std::vector<T>::size()); }

  void push_back(const T &value) {
    std::vector<T>::push_back(value);
    ++stopIndex;
  }

  size_t size() const { return stopIndex; }

  class Iterator {
   public:
    Iterator(Collection &v, size_t index) : vec(v), currentIndex(index) {}

    Iterator &operator++() {
      ++currentIndex;
      return *this;
    }

    bool operator!=(const Iterator &other) const { return currentIndex != other.vec.stopIndex; }

    T &operator*() { return vec[currentIndex]; }

   private:
    Collection &vec;
    size_t currentIndex;
  };

  Iterator begin() { return Iterator(*this, 0); }
  Iterator end() { return Iterator(*this, stopIndex); }
};

#endif /* Collection_hpp */
