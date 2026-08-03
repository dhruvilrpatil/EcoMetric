/**
 * src/components/atoms/SearchInput.tsx
 *
 * PRD §4.6 Inputs — search-input: white bg, 1px hairline border, 40px height, 2px radius
 * Used in: ecoinvent material search (Step 2), global nav search
 *
 * Fires onSearch callback with 300ms debounce (PRD Step 2 requirement).
 */

import { useEffect, useRef, useState, type InputHTMLAttributes } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faMagnifyingGlass, faSpinner, faXmark } from '@fortawesome/free-solid-svg-icons'

export interface SearchInputProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, 'onChange' | 'type'> {
  /** Visible label — required for accessibility */
  label: string
  /** Debounced search callback — fires 300ms after user stops typing */
  onSearch: (query: string) => void
  /** Show loading spinner during async search */
  loading?: boolean
  /** Debounce delay in ms. Default: 300 per PRD §6.5 requirement */
  debounceMs?: number
  /** Controlled value override */
  value?: string
  /** Allow clearing input with X button */
  clearable?: boolean
}

export function SearchInput({
  label,
  onSearch,
  loading = false,
  debounceMs = 300,
  value: externalValue,
  clearable = true,
  placeholder,
  id,
  className = '',
  ...rest
}: SearchInputProps) {
  const inputId = id ?? `search-${label.toLowerCase().replace(/\s+/g, '-')}`
  const [internalValue, setInternalValue] = useState(externalValue ?? '')
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Sync external value
  useEffect(() => {
    if (externalValue !== undefined) setInternalValue(externalValue)
  }, [externalValue])

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const val = e.target.value
    setInternalValue(val)

    // Clear previous debounce timer
    if (debounceRef.current) clearTimeout(debounceRef.current)

    // PRD §6.5: 300ms debounced search
    debounceRef.current = setTimeout(() => {
      onSearch(val)
    }, debounceMs)
  }

  function handleClear() {
    setInternalValue('')
    onSearch('')
  }

  // Cleanup on unmount
  useEffect(() => () => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
  }, [])

  return (
    <div className={`flex flex-col gap-xs ${className}`}>
      <label htmlFor={inputId} className="text-body-strong text-body">
        {label}
      </label>

      <div className="relative">
        {/* Search icon */}
        <span
          className="absolute left-lg top-1/2 -translate-y-1/2 text-stone pointer-events-none"
          aria-hidden="true"
        >
          {loading
            ? <FontAwesomeIcon icon={faSpinner} spin size="sm" />
            : <FontAwesomeIcon icon={faMagnifyingGlass} size="sm" />
          }
        </span>

        <input
          {...rest}
          id={inputId}
          type="search"
          role="searchbox"
          aria-label={label}
          value={internalValue}
          onChange={handleChange}
          placeholder={placeholder ?? `Search ${label.toLowerCase()}…`}
          className="search-input pl-xxl pr-xxl w-full"
        />

        {/* Clear button */}
        {clearable && internalValue && (
          <button
            type="button"
            onClick={handleClear}
            aria-label="Clear search"
            className="absolute right-lg top-1/2 -translate-y-1/2 text-stone hover:text-ink min-h-touch min-w-touch flex items-center justify-center"
          >
            <FontAwesomeIcon icon={faXmark} size="sm" />
          </button>
        )}
      </div>
    </div>
  )
}
